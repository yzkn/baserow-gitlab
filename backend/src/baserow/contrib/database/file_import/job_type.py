import json

from django.utils.encoding import force_str
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import translation
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from baserow.api.exceptions import RequestBodyValidationException
from baserow.api.utils import validate_data
from baserow.contrib.database.api.rows.serializers import get_row_serializer_class
from baserow.core.utils import grouper
from baserow.core.jobs.registries import JobType
from baserow.core.jobs.constants import JOB_FAILED, JOB_FINISHED
from baserow.contrib.database.views.signals import view_updated
from baserow.contrib.database.rows.handler import RowHandler

from .exceptions import FileImportMaxErrorCountExceeded
from .models import FileImportJob
from .constants import FILE_IMPORT_IN_PROGRESS, PRE_VALIDATION_IN_PROGRESS
from .serializers import (
    ReportSerializer,
)

BATCH_SIZE = 1024


def serialize_errors_recursive(error):
    if isinstance(error, dict):
        return {
            key: serialize_errors_recursive(errors) for key, errors in error.items()
        }
    elif isinstance(error, list):
        return [serialize_errors_recursive(errors) for errors in error]
    else:
        if isinstance(error, ValidationError):
            return {"error": error.message, "code": error.code}
        if isinstance(error, Exception):
            return {"error": force_str(error), "code": "unknown_error"}
        return error


def prepare_creation_report(creation_report, index_mapping):
    return {
        index_mapping[index]: {
            field: serialize_errors_recursive(errs)
            for field, errs in field_errs.items()
        }
        for index, field_errs in creation_report.items()
    }


class FileImportJobType(JobType):
    type = "file_import"

    model_class = FileImportJob

    max_count = 1

    request_serializer_field_names = []

    request_serializer_field_overrides = {}

    job_exceptions_map = {
        FileImportMaxErrorCountExceeded: f"This file import has raised too many "
        "errors.",
    }

    serializer_field_names = ["table_id", "report"]

    serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=True,
            help_text="Table id where data will be imported.",
        ),
        "report": ReportSerializer(help_text="Import report."),
    }

    def prepare_values(self, values, user):
        """
        Filter data from the values dict. Data are going to be added later as a file.
        See `.after_job_creation()`.
        """

        filtered_dict = dict(**values)
        filtered_dict.pop("data")
        return filtered_dict

    def after_job_creation(self, job, values):
        """
        Save the data file for the newly created job.
        """

        data_file = ContentFile(json.dumps(values["data"]))
        job.data_file.save(None, data_file)

    def clean_up_jobs(self):
        """
        Check if a job is not in failed or success status after the soft time limit.
        If so, the job is marked as failed and the data file is removed.
        """

        limit_date = timezone.now() - timezone.timedelta(
            seconds=(settings.BASEROW_JOB_SOFT_TIME_LIMIT + 1)
        )

        for job in FileImportJob.objects.filter(updated_on__lte=limit_date).exclude(
            state__in=[JOB_FAILED, JOB_FINISHED]
        ):
            try:
                job.data_file.delete()
            except ValueError:
                # File doesn't exist, that's ok
                pass

            job.state = JOB_FAILED
            job.human_readable_error = (
                f"Something went wrong during the file_import job execution."
            )
            job.error = "Unknown error"
            job.save()

    def on_error(self, job, error):
        if isinstance(error, FileImportMaxErrorCountExceeded):
            report = {
                key: value
                for key, value in list(error.report.items())[
                    : settings.BASEROW_MAX_FILE_IMPORT_ERROR_COUNT
                ]
            }
            job.report = {"failing_rows": report}
            job.save(update_fields=("report",))

    def run(self, job, progress):
        """
        Fills the provided table with the normalized data that needs to be created upon
        creation of the table.
        """

        data = []

        with job.data_file.open("r") as fin:
            data = json.load(fin)

        fields = list(job.table.field_set.all())

        # Here we assume the data has already been checked for shape and row length by
        # the job initiator.
        data = [
            {f"field_{fields[index].id}": value for index, value in enumerate(row)}
            for row in data
        ]

        report = {}
        # We want error messages to be translated with the user locale if possible
        with translation.override(job.user.profile.language):

            validation_sub_progress = progress.create_child(50, len(data))
            validation_sub_progress.increment(state=PRE_VALIDATION_IN_PROGRESS)

            # STEP 1: prevalidate data with serializer
            valid_data = []
            model = job.table.get_model()
            validation_serializer = get_row_serializer_class(model)
            for count, chunk in enumerate(grouper(BATCH_SIZE, data)):
                row_start_index = count * BATCH_SIZE
                try:
                    validate_data(validation_serializer, list(chunk), many=True)
                except RequestBodyValidationException as e:
                    report.update(
                        {
                            row_start_index + index: err
                            for index, err in enumerate(e.detail["detail"])
                            if err
                        }
                    )

                # Creates an index mapping to handle the shift created by missing rows
                # for report the row creation report.
                index_mapping = {}
                for index, row in enumerate(chunk):
                    if index + row_start_index not in report:
                        index_mapping[len(valid_data)] = index + row_start_index
                        valid_data.append(row)

                validation_sub_progress.increment(len(chunk))
                if len(report) > settings.BASEROW_MAX_FILE_IMPORT_ERROR_COUNT:
                    raise FileImportMaxErrorCountExceeded(report)

            creation_sub_progress = progress.create_child(50, len(data))
            creation_sub_progress.increment(state=FILE_IMPORT_IN_PROGRESS)

            val_error_count = len(report)

            # Callback for row creation progress
            def on_progress(row_count, creation_report):
                creation_sub_progress.increment(row_count)

                if (
                    val_error_count + len(creation_report)
                    > settings.BASEROW_MAX_FILE_IMPORT_ERROR_COUNT
                ):
                    report.update(
                        prepare_creation_report(creation_report, index_mapping)
                    )
                    raise FileImportMaxErrorCountExceeded(report)

            # STEP 2: create rows in DB
            row_handler = RowHandler()
            _, creation_report = row_handler.create_rows(
                user=job.user,
                table=job.table,
                model=model,
                rows_values=valid_data,
                import_mode=True,
                on_progress=on_progress,
            )

            report.update(prepare_creation_report(creation_report, index_mapping))

        def after_commit():
            """
            Removes the data file to save space and save the error report.
            """

            job.refresh_from_db()
            job.data_file.delete()
            job.report = {"failing_rows": report}
            job.save()

        transaction.on_commit(after_commit)

        # The signal is sent on_commit
        for view in job.table.view_set.all():
            view_updated.send(self, view=view, user=None, force_table_refresh=True)

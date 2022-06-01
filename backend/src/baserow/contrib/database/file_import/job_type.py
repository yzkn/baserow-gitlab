import json

from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import translation
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from baserow.core.utils import grouper
from baserow.core.jobs.registries import JobType
from baserow.core.jobs.constants import JOB_FAILED, JOB_FINISHED
from baserow.contrib.database.views.signals import view_updated

from .models import FileImportJob
from .constants import FILE_IMPORT_IN_PROGRESS
from .serializers import (
    ReportSerializer,
)


BATCH_SIZE = 1024


class FileImportJobType(JobType):
    type = "file_import"

    model_class = FileImportJob

    max_count = 1

    request_serializer_field_names = []

    request_serializer_field_overrides = {}

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
            minutes=(settings.BASEROW_JOB_SOFT_TIME_LIMIT + 1)
        )

        for job in FileImportJob.objects.filter(updated_on__lte=limit_date).exclude(
            state__in=[JOB_FAILED, JOB_FINISHED]
        ):
            try:
                job.data_file.delete()
            except ValueError:
                pass
            job.state = JOB_FAILED
            job.human_readable_error = (
                f"Something went wrong during the file_import job execution."
            )
            job.error = "Unknown error"
            job.save()

    def run(self, job, progress):
        """
        Fills the provided table with the normalized data that needs to be created upon
        creation of the table.
        """

        data = []

        table = job.table

        model = table.get_model()
        fields = list(table.field_set.all())

        with job.data_file.open("r") as fin:
            data = json.load(fin)

        sub_progress = progress.create_child(100, len(data))

        sub_progress.increment(state=FILE_IMPORT_IN_PROGRESS)

        report = {"failing_rows": []}

        # We split the import in batch to be able to track the job progress
        for count, chunk in enumerate(grouper(BATCH_SIZE, data)):
            bulk_data = []
            for index, row in enumerate(chunk):
                real_index = count * BATCH_SIZE + index
                instance = model(
                    order=real_index + 1,
                    **{
                        f"field_{fields[index].id}": value
                        for index, value in enumerate(row)
                    },
                )
                try:
                    instance.full_clean()
                except ValidationError as e:

                    with translation.override(job.user.profile.language):
                        report["failing_rows"].append(
                            {"index": real_index, "errors": e.message_dict}
                        )
                else:
                    bulk_data.append(instance)

            model.objects.bulk_create(bulk_data)

            sub_progress.increment(
                len(chunk),
                state=FILE_IMPORT_IN_PROGRESS,
            )

        def after_commit():
            job.refresh_from_db()
            job.data_file.delete()
            job.report = report
            job.save()

        # Remove the file after the commit to save space
        transaction.on_commit(after_commit)

        # The signal is sent on_commit
        for view in table.view_set.all():
            view_updated.send(self, view=view, user=None, force_table_refresh=True)

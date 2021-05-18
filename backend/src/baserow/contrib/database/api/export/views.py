from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import validate_body, map_exceptions
from baserow.api.errors import (
    ERROR_USER_NOT_IN_GROUP,
    ERROR_USER_INVALID_GROUP_PERMISSIONS,
)
from baserow.api.schemas import get_error_schema
from baserow.contrib.database.api.export.errors import (
    ExportJobDoesNotExistException,
    ERROR_EXPORT_JOB_DOES_NOT_EXIST,
)
from baserow.contrib.database.api.export.serializers import (
    GetExportJobSerializer,
    CreateExportJobSerializer,
)
from baserow.contrib.database.api.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.api.views.errors import ERROR_VIEW_DOES_NOT_EXIST
from baserow.contrib.database.export.handler import ExportHandler
from baserow.contrib.database.export.models import ExportJob
from baserow.contrib.database.export.tasks import run_export_job
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.exceptions import ViewDoesNotExist
from baserow.contrib.database.views.handler import ViewHandler
from baserow.core.exceptions import UserNotInGroup, UserInvalidGroupPermissionsError


class ExportTableView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Exports the table with this id if you have permissions "
                "to access it.",
            )
        ],
        tags=["Export"],
        operation_id="export_table",
        description=(
            "Exports the specified table to any of the supported exported file formats"
        ),
        request=CreateExportJobSerializer,
        responses={
            200: GetExportJobSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                ]
            ),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(CreateExportJobSerializer)
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def post(self, request, table_id, data):
        """
        Starts a new export job for the provided table, export type and options.
        """
        table = TableHandler().get_table(table_id)
        table.database.group.has_user(request.user, raise_error=True)

        exporter_type = data.pop("exporter_type")

        return _create_and_start_new_job(request.user, table, None, exporter_type, data)


def _create_and_start_new_job(user, table, view, exporter_type, export_options):
    job = ExportHandler().create_pending_export_job(
        user, table, view, exporter_type, export_options
    )
    run_export_job.delay(job.id)
    return Response(GetExportJobSerializer(job).data)


class ExportViewView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="view_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Exports the view with this id if you have permissions "
                "to access it.",
            )
        ],
        tags=["Export"],
        operation_id="export_view",
        description=(
            "Exports the specified view to any of the supported exported file formats"
        ),
        request=CreateExportJobSerializer,
        responses={
            200: GetExportJobSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_USER_INVALID_GROUP_PERMISSIONS",
                ]
            ),
            404: get_error_schema(["ERROR_VIEW_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(CreateExportJobSerializer)
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ViewDoesNotExist: ERROR_VIEW_DOES_NOT_EXIST,
            UserInvalidGroupPermissionsError: ERROR_USER_INVALID_GROUP_PERMISSIONS,
        }
    )
    def post(self, request, view_id, data):
        """
        Starts a new export job for the provided view, export type and options.
        """
        view = ViewHandler().get_view(view_id)
        view.table.database.group.has_user(request.user, raise_error=True)

        exporter_type = data.pop("exporter_type")

        return _create_and_start_new_job(
            request.user,
            view.table,
            view,
            exporter_type,
            data,
        )


class ExportJobView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="job_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The job id to get.",
            )
        ],
        tags=["Export"],
        operation_id="get_export_job",
        description=(
            "Returns information on the specified export job if the user has access."
        ),
        responses={
            200: GetExportJobSerializer,
            400: get_error_schema(
                [
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_EXPORT_JOB_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            ExportJobDoesNotExistException: ERROR_EXPORT_JOB_DOES_NOT_EXIST,
        }
    )
    def get(self, request, job_id):
        """
        Retrieves the specified export job.
        """
        try:
            job = ExportJob.objects.get(id=job_id)
        except ExportJob.DoesNotExist:
            raise ExportJobDoesNotExistException()

        if job.user != request.user:
            raise ExportJobDoesNotExistException()

        return Response(GetExportJobSerializer(job).data)

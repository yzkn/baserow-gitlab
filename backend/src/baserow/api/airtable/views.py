from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import transaction

from baserow.api.schemas import get_error_schema
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP, ERROR_GROUP_DOES_NOT_EXIST
from baserow.core.exceptions import UserNotInGroup, GroupDoesNotExist
from baserow.core.handler import CoreHandler
from baserow.contrib.database.airtable.models import AirtableImportJob
from baserow.contrib.database.airtable.exceptions import (
    AirtableImportJobDoesNotExist,
    AirtableImportJobAlreadyRunning,
)
from baserow.contrib.database.airtable.handler import (
    get_airtable_import_job,
    create_and_start_airtable_import_job,
)

from .serializers import AirtableImportJobSerializer, CreateAirtableImportJobSerializer
from .errors import (
    ERROR_AIRTABLE_IMPORT_JOB_DOES_NOT_EXIST,
    ERROR_AIRTABLE_JOB_ALREADY_RUNNING,
)


class AirtableImportJobsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Database airtable import"],
        operation_id="create_airtable_import_job",
        description=("@TODO"),
        responses={
            200: AirtableImportJobSerializer,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_AIRTABLE_JOB_ALREADY_RUNNING"]
            ),
        },
    )
    @map_exceptions(
        {
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            AirtableImportJobAlreadyRunning: ERROR_AIRTABLE_JOB_ALREADY_RUNNING,
        }
    )
    @validate_body(CreateAirtableImportJobSerializer)
    @transaction.atomic
    def post(self, request, data):
        group = CoreHandler().get_group(data["group_id"])
        airtable_share_id = data["airtable_share_url"]  # @TODO convert value to ID
        job = create_and_start_airtable_import_job(
            request.user, group, airtable_share_id
        )
        return Response(AirtableImportJob(job).data)


class AirtableImportJobView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Database airtable import"],
        operation_id="get_airtable_import_job",
        description=("@TODO"),
        responses={
            200: AirtableImportJobSerializer,
            404: get_error_schema(["ERROR_AIRTABLE_IMPORT_JOB_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            AirtableImportJobDoesNotExist: ERROR_AIRTABLE_IMPORT_JOB_DOES_NOT_EXIST,
        }
    )
    def get(self, request, job_id):
        job = get_airtable_import_job(request.user, job_id)
        return Response(AirtableImportJob(job).data)

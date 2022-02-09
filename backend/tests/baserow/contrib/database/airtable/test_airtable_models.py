import pytest


from baserow.contrib.database.airtable.models import AirtableImportJob
from baserow.contrib.database.airtable.constants import (
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES,
    AIRTABLE_EXPORT_JOB_CONVERTING,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_BASE,
)


@pytest.mark.django_db
def test_is_running_queryset(data_fixture):
    data_fixture.create_airtable_import_job(
        state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED
    )
    data_fixture.create_airtable_import_job(
        state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED
    )

    assert AirtableImportJob.objects.is_running().count() == 0

    data_fixture.create_airtable_import_job(
        state=AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING
    )
    data_fixture.create_airtable_import_job(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES)
    data_fixture.create_airtable_import_job(state=AIRTABLE_EXPORT_JOB_CONVERTING)
    data_fixture.create_airtable_import_job(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_BASE)

    assert AirtableImportJob.objects.is_running().count() == 4

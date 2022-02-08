import pytest
import responses

from unittest.mock import patch

from baserow.core.utils import Progress
from baserow.contrib.database.airtable.tasks import run_import_from_airtable
from baserow.contrib.database.airtable.models import AirtableImportJob
from baserow.contrib.database.airtable.constants import (
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED,
)


@pytest.mark.django_db
@responses.activate
@patch("baserow.contrib.database.airtable.handler.import_from_airtable_to_group")
def test_run_import_from_airtable(mock_import_from_airtable_to_group, data_fixture):
    def update_progress_slow(*args, **kwargs):
        nonlocal job
        progress = kwargs["parent_progress"]
        progress[0].increment(50, "test")
        job.refresh_from_db()
        assert job.progress_percentage == 50
        assert job.state == "test"
        progress[0].increment(50)

    mock_import_from_airtable_to_group.side_effect = update_progress_slow

    job = data_fixture.create_airtable_import_job()

    with pytest.raises(AirtableImportJob.DoesNotExist):
        run_import_from_airtable(0)

    run_import_from_airtable(job.id)

    mock_import_from_airtable_to_group.assert_called_once()
    args = mock_import_from_airtable_to_group.call_args
    assert args[0][0].id == job.group.id
    assert args[0][1] == job.airtable_share_id
    assert isinstance(args[1]["parent_progress"][0], Progress)
    assert args[1]["parent_progress"][1] == 100

    job.refresh_from_db()
    assert job.progress_percentage == 100
    assert job.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED


@pytest.mark.django_db
@responses.activate
@patch("baserow.contrib.database.airtable.handler.import_from_airtable_to_group")
def test_run_import_from_airtable_failing_import(
    mock_import_from_airtable_to_group, data_fixture
):
    def update_progress_slow(*args, **kwargs):
        raise Exception("test-1")

    mock_import_from_airtable_to_group.side_effect = update_progress_slow

    job = data_fixture.create_airtable_import_job()
    run_import_from_airtable(job.id)

    job.refresh_from_db()
    assert job.state == AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED
    assert job.error == "test-1"

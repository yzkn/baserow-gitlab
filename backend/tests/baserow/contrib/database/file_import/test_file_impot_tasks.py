import pytest
from pyinstrument import Profiler
from freezegun import freeze_time
from unittest.mock import patch

from django.utils import timezone

from baserow.core.jobs.tasks import run_async_job, clean_up_jobs
from baserow.core.jobs.constants import (
    JOB_FAILED,
    JOB_FINISHED,
    JOB_PENDING,
)


@pytest.mark.django_db(transaction=True)
def test_run_file_import_task(data_fixture):

    job = data_fixture.create_file_import_job()
    table = job.table

    run_async_job(job.id)

    job.refresh_from_db()
    assert job.state == JOB_FINISHED
    assert job.progress_percentage == 100

    model = table.get_model()
    rows = model.objects.all()

    assert len(rows) == 5

    # A table with non string field
    user = data_fixture.create_user()
    table, _, _ = data_fixture.build_table(
        columns=[
            (f"col1", "text"),
            (f"col2", "number"),
            (f"col3", "url"),
        ],
        rows=[],
        user=user,
    )

    data = [["foo", 1, "http://test.en"], ["bar", 2, "http://example.com"]]

    job = data_fixture.create_file_import_job(user=user, table=table, data=data)
    run_async_job(job.id)

    model = table.get_model()
    field1, field2, field3 = table.field_set.all()
    rows = model.objects.all()

    assert len(rows) == 2

    job.refresh_from_db()
    with pytest.raises(ValueError):
        # Check that the data file has been removed
        job.data_file.path

    # Import data to an existing table
    data = [["baz", 3, "http://example.com"], ["bob", 4, "http://example.com"]]
    job = data_fixture.create_file_import_job(user=user, table=table, data=data)
    run_async_job(job.id)

    rows = model.objects.all()
    assert len(rows) == 4

    # Import data with error
    data = [
        ["good", 2.3, "Not an URL"],
        ["good", "ugly", "http://example.com"],
        [None, None, None],
    ]
    job = data_fixture.create_file_import_job(user=user, table=table, data=data)
    run_async_job(job.id)

    rows = model.objects.all()
    assert len(rows) == 5

    job.refresh_from_db()

    assert job.report["failing_rows"][0]["index"] == 0
    assert job.report["failing_rows"][0]["errors"] == {
        f"field_{field2.id}": ["Ensure that there are no more than 0 decimal places."],
        f"field_{field3.id}": ["Enter a valid value."],
    }

    assert job.report["failing_rows"][1]["index"] == 1
    assert job.report["failing_rows"][1]["errors"] == {
        f"field_{field2.id}": ["“ugly” value must be a decimal number."]
    }

    # Change user language to test message i18n
    user.profile.language = "fr"
    user.profile.save()

    # Translate messages
    data = [["good", "ugly"]]
    job = data_fixture.create_file_import_job(user=user, table=table, data=data)
    run_async_job(job.id)

    job.refresh_from_db()

    assert job.report["failing_rows"][0]["errors"][f"field_{field2.id}"] == [
        "La valeur «\xa0ugly\xa0» doit être un nombre décimal."
    ]


@pytest.mark.django_db(transaction=True)
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
def test_run_file_import_task_big_data(data_fixture):

    row_count = 100_000

    job = data_fixture.create_file_import_job(column_count=100, row_count=row_count)
    table = job.table

    profiler = Profiler()
    profiler.start()
    run_async_job(job.id)
    profiler.stop()

    job.refresh_from_db()
    assert job.state == JOB_FINISHED
    assert job.progress_percentage == 100

    model = table.get_model()
    rows = model.objects.all()
    assert rows.count() == row_count

    print(profiler.output_text(unicode=True, color=True, show_all=True))


@pytest.mark.django_db
@patch("baserow.contrib.database.export.handler.default_storage")
def test_cleanup_file_import_job(storage_mock, data_fixture, settings):
    now = timezone.now()
    time_before_soft_limit = now - timezone.timedelta(
        minutes=settings.BASEROW_JOB_SOFT_TIME_LIMIT + 1
    )
    # create recent job
    with freeze_time(now):
        job1 = data_fixture.create_file_import_job()

    # Create old jobs
    with freeze_time(time_before_soft_limit):
        job2 = data_fixture.create_file_import_job()
        job3 = data_fixture.create_file_import_job(state=JOB_FINISHED)

    with freeze_time(now):
        clean_up_jobs()

    job1.refresh_from_db()
    assert job1.state == JOB_PENDING

    job2.refresh_from_db()
    assert job2.state == JOB_FAILED
    assert job2.updated_on == now

    with pytest.raises(ValueError):
        job2.data_file.path

    job3.refresh_from_db()
    assert job3.state == JOB_FINISHED
    assert job3.updated_on == time_before_soft_limit

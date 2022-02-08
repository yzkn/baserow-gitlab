from django.db import transaction

from baserow.config.celery import app


@app.task(bind=True, queue="export")
def run_import_from_airtable(self, job_id):
    """
    @TODO docs
    """

    from baserow.core.utils import Progress
    from baserow.contrib.database.airtable.models import AirtableImportJob
    from baserow.contrib.database.airtable.handler import import_from_airtable_to_group
    from baserow.contrib.database.airtable.constants import (
        AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED,
        AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED,
    )

    job = AirtableImportJob.objects.select_related("group").get(id=job_id)

    def progress_updated(percentage, state):
        nonlocal job

        if job.progress_percentage != percentage:
            job.progress_percentage = percentage
            changed = True

        if state is not None and job.state != state:
            job.state = state
            changed = True

        if changed:
            job.save()

    progress = Progress(100)
    progress.register_updated_event(progress_updated)

    with transaction.atomic():
        try:
            import_from_airtable_to_group(
                job.group, job.airtable_share_id, parent_progress=(progress, 100)
            )
            job.state = AIRTABLE_EXPORT_JOB_DOWNLOADING_FINISHED
            job.save()
        except Exception as e:
            job.state = AIRTABLE_EXPORT_JOB_DOWNLOADING_FAILED
            job.error = str(e)
            job.save()

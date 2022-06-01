import logging
from typing import Optional, Type

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.core.cache import cache
from django.db.models import QuerySet
from django.utils import timezone
from django.conf import settings

from baserow.core.utils import Progress

from .types import AnyJob
from .registries import job_type_registry
from .exceptions import (
    JobDoesNotExist,
    MaxJobCountExceeded,
)
from .models import Job
from .tasks import run_async_job

from .cache import job_progress_key
from .constants import JOB_FAILED, JOB_FINISHED

logger = logging.getLogger(__name__)


class JobHandler:
    def run(self, job: AnyJob):
        def progress_updated(percentage, state):
            """
            Every time the progress of the import changes, this callback function is
            called. If the percentage or the state has changed, the job will be updated.
            """

            nonlocal job

            if job.progress_percentage != percentage:
                job.progress_percentage = percentage
                changed = True

            if state is not None and job.state != state:
                job.state = state
                changed = True

            if changed:
                # The progress must also be stored in the Redis cache. Because we're
                # currently in a transaction, other database connections don't know
                # about the progress and this way, we can still communicate it to
                # the user.
                cache.set(
                    job_progress_key(job.id),
                    {
                        "progress_percentage": job.progress_percentage,
                        "state": job.state,
                    },
                    timeout=None,
                )
                job.save()

        progress = Progress(100)
        progress.register_updated_event(progress_updated)

        job_type = job_type_registry.get_by_model(job.specific_class)

        return job_type.run(job.specific, progress)

    @staticmethod
    def get_job(
        user: AbstractUser,
        job_id: int,
        job_model: Optional[Type[AnyJob]] = None,
        base_queryset: Optional[QuerySet] = None,
    ) -> Job:
        """Returns the job corresponding to the given id."""

        if not job_model:
            job_model = Job

        if base_queryset is None:
            base_queryset = job_model.objects

        try:
            return base_queryset.select_related("user").get(id=job_id, user_id=user.id)
        except Job.DoesNotExist:
            raise JobDoesNotExist(f"The job with id {job_id} does not exist.")

    def create_and_start_job(
        self, user: AbstractUser, job_type_name: str, **kwargs
    ) -> Job:
        """Creates a new job and schedule the asynchronous task."""

        job_type = job_type_registry.get(job_type_name)
        model_class = job_type.model_class

        # Check how many job of same type are running simultaneously. If count > max
        # we don't want to create a new one.
        running_jobs = model_class.objects.filter(user_id=user.id).is_running()
        if len(running_jobs) >= job_type.max_count:
            raise MaxJobCountExceeded(
                f"You can only launch {job_type.max_count} {job_type_name} job(s) at "
                "the same time."
            )

        job_values = job_type.prepare_values(kwargs, user)
        job = model_class.objects.create(user=user, **job_values)
        job_type.after_job_creation(job, kwargs)

        transaction.on_commit(lambda: run_async_job.delay(job.id))
        return job

    def clean_up_jobs(self):
        """
        Execute the cleanup method of all job types and remove expired jobs.
        """

        for job_type in job_type_registry.get_all():
            job_type.clean_up_jobs()

        limit_date = timezone.now() - timezone.timedelta(
            minutes=(settings.BASEROW_JOB_EXPIRATION_TIME_LIMIT)
        )
        Job.objects.filter(
            updated_on__lte=limit_date,
            state__in=[JOB_FAILED, JOB_FINISHED],
        ).delete()

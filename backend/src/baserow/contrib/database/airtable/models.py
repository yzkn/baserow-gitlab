from django.db import models
from django.contrib.auth import get_user_model

from baserow.core.models import Group
from baserow.core.mixins import CreatedAndUpdatedOnMixin

from .constants import AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING

User = get_user_model()


class AirtableImportJob(CreatedAndUpdatedOnMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    airtable_share_id = models.CharField(max_length=18)
    progress_percentage = models.IntegerField(default=0)
    state = models.CharField(
        max_length=128, default=AIRTABLE_EXPORT_JOB_DOWNLOADING_PENDING
    )
    error = models.TextField(blank=True, default="")

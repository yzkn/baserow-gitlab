import dataclasses
import json

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class JSONEncoderSupportingDataClasses(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class Action(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    type = models.TextField()
    params = models.JSONField(encoder=JSONEncoderSupportingDataClasses)
    scope = models.TextField()
    undone_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_on",)
        indexes = [models.Index(fields=["user", "-created_on", "scope"])]


class ActionLog(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)

    created_on = models.DateTimeField(auto_now_add=True)
    type = models.TextField()
    params = models.JSONField(encoder=JSONEncoderSupportingDataClasses)
    scope = models.TextField()
    log_type = models.TextField()

    class Meta:
        ordering = ("-created_on",)
        indexes = [models.Index(fields=["user", "-created_on", "scope"])]

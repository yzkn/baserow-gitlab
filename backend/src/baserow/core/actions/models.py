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
    session = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    type = models.TextField()
    params = models.JSONField(encoder=JSONEncoderSupportingDataClasses)
    category = models.TextField()
    undone_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    def __str__(self):
        return (
            f"Action(user={self.user_id}, type={self.type}, category={self.category}, "
            f"created_on={self.created_on},  undone_at={self.undone_at}, params="
            f"{self.params}, \nsession={self.session})"
        )

    class Meta:
        ordering = ("-created_on",)
        # TODO think/test indexes
        indexes = [models.Index(fields=["user", "-created_on", "category", "session"])]

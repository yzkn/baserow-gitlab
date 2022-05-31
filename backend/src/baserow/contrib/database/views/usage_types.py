from django.db.models import Sum

from baserow.contrib.database.views.models import FormView
from baserow.core.usage.registries import GroupStorageUsageItemType


class FormViewGroupStorageUsageItem(GroupStorageUsageItemType):
    type = "form_view"

    def calculate_storage_usage(self, group_id: int) -> int:
        cover_image_usage = FormView.objects.filter(
            table__database__group=group_id, cover_image__isnull=False
        ).aggregate(sum=Sum("cover_image__size"))["sum"]

        if cover_image_usage is None:
            cover_image_usage = 0

        logo_image_usage = FormView.objects.filter(
            table__database__group=group_id, logo_image__isnull=False
        ).aggregate(sum=Sum("logo_image__size"))["sum"]

        if logo_image_usage is None:
            logo_image_usage = 0

        return cover_image_usage + logo_image_usage

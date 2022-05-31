from baserow.core.models import Group
from baserow.core.usage.registries import group_storage_usage_item_registry


class UsageHandler:
    @classmethod
    def calculate_storage_usage(cls):
        for group in Group.objects.filter(template__isnull=True):
            total = 0
            for item in group_storage_usage_item_registry.get_all():
                total += item.calculate_storage_usage(group.id)

            group.storage_usage = total
            group.save()

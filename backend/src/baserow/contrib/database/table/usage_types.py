from baserow.contrib.database.fields.field_types import FileFieldType
from baserow.contrib.database.table.models import Table
from baserow.core.usage.registries import GroupStorageUsageItemType


class TableGroupStorageUsageItemType(GroupStorageUsageItemType):
    type = "table"

    def calculate_storage_usage(self, group_id: int) -> int:
        total = 0
        for table in Table.objects.filter(database__group=group_id):
            model = table.get_model()

            file_fields = []
            for field in model._field_objects.values():
                if type(field.get("type")) is FileFieldType:
                    file_fields.append(field.get("name"))

            if len(file_fields) > 0:
                for row in model.objects.all():
                    for file_field in file_fields:
                        for file in getattr(row, file_field):
                            total += file["size"]

        return total

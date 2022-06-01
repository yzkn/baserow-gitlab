import pytest

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.usage_types import TableGroupStorageUsageItemType


@pytest.mark.django_db
def test_table_group_storage_usage_item_type(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(user=user, database=database)
    file_field = data_fixture.create_file_field(table=table)

    usage = TableGroupStorageUsageItemType().calculate_storage_usage(group.id)

    assert usage == 0

    user_file_1 = data_fixture.create_user_file(
        original_name="test.png", is_image=True, size=500
    )

    RowHandler().create_row(user, table, {file_field.id: [{"name": user_file_1.name}]})

    usage = TableGroupStorageUsageItemType().calculate_storage_usage(group.id)

    assert usage == 500

    user_file_2 = data_fixture.create_user_file(
        original_name="another_file", is_image=True, size=200
    )

    RowHandler().create_row(user, table, {file_field.id: [{"name": user_file_2.name}]})

    usage = TableGroupStorageUsageItemType().calculate_storage_usage(group.id)

    assert usage == 700

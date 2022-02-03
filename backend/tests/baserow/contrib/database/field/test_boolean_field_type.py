import pytest

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.field_types import BooleanFieldType


@pytest.mark.django_db
def test_alter_boolean_field_column_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, order=1)

    handler = FieldHandler()
    field = handler.update_field(user=user, field=field, name="Text field")

    model = table.get_model()
    mapping = {
        "1": True,
        "t": True,
        "y": True,
        "yes": True,
        "on": True,
        "YES": True,
        "": False,
        "f": False,
        "n": False,
        "false": False,
        "off": False,
        "Random text": False,
    }

    for value in mapping.keys():
        model.objects.create(**{f"field_{field.id}": value})

    # Change the field type to a number and test if the values have been changed.
    field = handler.update_field(user=user, field=field, new_type_name="boolean")

    model = table.get_model()
    rows = model.objects.all()

    for index, value in enumerate(mapping.values()):
        assert getattr(rows[index], f"field_{field.id}") == value


@pytest.mark.django_db
def test_get_set_export_serialized_value_boolean_field(data_fixture):
    table = data_fixture.create_database_table()
    boolean_field = data_fixture.create_boolean_field(table=table)
    boolean_field_name = f"field_{boolean_field.id}"
    boolean_field_type = field_type_registry.get_by_model(boolean_field)

    model = table.get_model()
    row_1 = model.objects.create()
    row_2 = model.objects.create(**{f"field_{boolean_field.id}": True})
    row_3 = model.objects.create(**{f"field_{boolean_field.id}": False})

    row_1.refresh_from_db()
    row_2.refresh_from_db()
    row_3.refresh_from_db()

    old_row_1_value = getattr(row_1, boolean_field_name)
    old_row_2_value = getattr(row_2, boolean_field_name)
    old_row_3_value = getattr(row_3, boolean_field_name)

    boolean_field_type.set_import_serialized_value(
        row_1,
        boolean_field_name,
        boolean_field_type.get_export_serialized_value(
            row_1, boolean_field_name, {}, None, None
        ),
        {},
        None,
        None,
    )
    boolean_field_type.set_import_serialized_value(
        row_2,
        boolean_field_name,
        boolean_field_type.get_export_serialized_value(
            row_2, boolean_field_name, {}, None, None
        ),
        {},
        None,
        None,
    )
    boolean_field_type.set_import_serialized_value(
        row_3,
        boolean_field_name,
        boolean_field_type.get_export_serialized_value(
            row_3, boolean_field_name, {}, None, None
        ),
        {},
        None,
        None,
    )

    row_1.save()
    row_2.save()
    row_3.save()

    row_1.refresh_from_db()
    row_2.refresh_from_db()
    row_3.refresh_from_db()

    assert old_row_1_value == getattr(row_1, boolean_field_name)
    assert old_row_2_value == getattr(row_2, boolean_field_name)
    assert old_row_3_value == getattr(row_3, boolean_field_name)


@pytest.mark.django_db
def test_airtable_import_checkbox_field(data_fixture, api_client):
    airtable_field = {
        "id": "fldTn59fpliSFcwpFA9",
        "name": "Checkbox",
        "type": "checkbox",
        "typeOptions": {"color": "green", "icon": "check"},
    }
    baserow_field, field_type = field_type_registry.from_airtable_field_to_serialized(
        airtable_field
    )
    assert baserow_field == {"type": BooleanFieldType.type}
    assert isinstance(field_type, BooleanFieldType)
    assert (
        field_type.from_airtable_column_value_to_serialized(
            {}, airtable_field, baserow_field, True, {}
        )
        == "true"
    )
    assert (
        field_type.from_airtable_column_value_to_serialized(
            {}, airtable_field, baserow_field, False, {}
        )
        == "false"
    )

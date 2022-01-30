import pytest

from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.field_types import TextFieldType


@pytest.mark.django_db
def test_airtable_import_long_text_field(data_fixture, api_client):
    airtable_field = {"id": "fld97w8Zq7Guyi448", "name": "Name", "type": "text2"}
    baserow_field, field_type = field_type_registry.from_airtable_field_to_serialized(
        airtable_field
    )
    assert baserow_field is None
    assert field_type is None

    airtable_field = {"id": "fld97w8Zq7Guyi448", "name": "Name", "type": "text"}
    baserow_field, field_type = field_type_registry.from_airtable_field_to_serialized(
        airtable_field
    )
    assert baserow_field == {"type": TextFieldType.type}
    assert isinstance(field_type, TextFieldType)

    assert (
        field_type.from_airtable_column_value_to_serialized(
            {}, airtable_field, baserow_field, "test", {}
        )
        == "test"
    )

import pytest

from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.field_types import PhoneNumberFieldType


@pytest.mark.django_db
def test_airtable_import_phone_field(data_fixture, api_client):
    airtable_field = {"id": "fldkrPuYJTqq7vSJ7Oh", "name": "Phone", "type": "phone"}
    baserow_field, field_type = field_type_registry.from_airtable_field_to_serialized(
        airtable_field
    )
    assert baserow_field == {"type": PhoneNumberFieldType.type}
    assert isinstance(field_type, PhoneNumberFieldType)

    assert (
        field_type.from_airtable_column_value_to_serialized(
            {}, airtable_field, baserow_field, "NOT_PHONE", {}
        )
        == ""
    )
    assert (
        field_type.from_airtable_column_value_to_serialized(
            {}, airtable_field, baserow_field, "1234", {}
        )
        == "1234"
    )

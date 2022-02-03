import pytest

from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.field_types import EmailFieldType


@pytest.mark.django_db
def test_airtable_import_email_field(data_fixture, api_client):
    airtable_field = {
        "id": "fldNdoAZRim39AxR9Eg",
        "name": "Email",
        "type": "text",
        "typeOptions": {"validatorName": "email"},
    }
    baserow_field, field_type = field_type_registry.from_airtable_field_to_serialized(
        airtable_field
    )
    assert baserow_field == {"type": EmailFieldType.type}
    assert isinstance(field_type, EmailFieldType)

    assert (
        field_type.from_airtable_column_value_to_serialized(
            {}, airtable_field, baserow_field, "NOT_EMAIL", {}
        )
        == ""
    )
    assert (
        field_type.from_airtable_column_value_to_serialized(
            {}, airtable_field, baserow_field, "test@test.nl", {}
        )
        == "test@test.nl"
    )

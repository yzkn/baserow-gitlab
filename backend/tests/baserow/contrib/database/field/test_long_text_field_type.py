import pytest

from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.field_types import LongTextFieldType


@pytest.mark.django_db
def test_airtable_import_text_field(data_fixture, api_client):
    airtable_field = {
        "id": "fldG9y88Zw7q7u4Z7i4",
        "name": "Name",
        "type": "multilineText",
    }
    baserow_field, field_type = field_type_registry.from_airtable_field_to_serialized(
        airtable_field
    )
    assert baserow_field == {"type": LongTextFieldType.type}
    assert isinstance(field_type, LongTextFieldType)

    assert (
        field_type.from_airtable_column_value_to_serialized(
            {}, airtable_field, baserow_field, "test", {}
        )
        == "test"
    )


@pytest.mark.django_db
def test_airtable_import_rich_text_field(data_fixture, api_client):
    airtable_field = {
        "id": "fldG9y88Zw7q7u4Z7i4",
        "name": "Name",
        "type": "richText",
    }
    baserow_field, field_type = field_type_registry.from_airtable_field_to_serialized(
        airtable_field
    )
    assert baserow_field == {"type": LongTextFieldType.type}
    assert isinstance(field_type, LongTextFieldType)

    content = {
        "otDocumentId": "otdHtbNg2tJKWj62WMn",
        "revision": 4,
        "documentValue": [
            {"insert": "Vestibulum", "attributes": {"bold": True}},
            {"insert": " ante ipsum primis in faucibus orci luctus et ultrices "},
            {"insert": "posuere", "attributes": {"italic": True}},
            {"insert": " cubilia curae; Class aptent taciti sociosqu ad litora."},
        ],
    }
    assert (
        field_type.from_airtable_column_value_to_serialized(
            {}, airtable_field, baserow_field, content, {}
        )
        == "Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere "
        "cubilia curae; Class aptent taciti sociosqu ad litora."
    )

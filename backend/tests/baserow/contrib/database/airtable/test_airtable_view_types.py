import pytest
import responses

from pytz import UTC
from baserow.contrib.database.views.models import GridView
from baserow.contrib.database.airtable.airtable_view_types import GridAirtableViewType
from baserow.contrib.database.airtable.registry import airtable_view_type_registry


@pytest.mark.django_db
@responses.activate
def test_unkown_view_type():
    airtable_view = {
        "id": "viwDgBCKTEdCQoHTQKH",
        "name": "With filters and sorts",
        "type": "unknown",
        "personalForUserId": None,
        "createdByUserId": "usrdGm7k7NIVWhK7W7L",
    }
    airtable_view_data = {}
    (
        baserow_view,
        airtable_view_type,
    ) = airtable_view_type_registry.from_airtable_view_to_instance(
        airtable_view, airtable_view_data, UTC
    )
    assert baserow_view is None
    assert airtable_view_type is None


@pytest.mark.django_db
@responses.activate
def test_grid_view_type(django_assert_num_queries):
    table = {
        "id": "tblRpq315qnnIcg5IjI",
        "name": "Users",
        "primaryColumnId": "fldG9y88Zw7q7u4Z7i4",
        "columns": [
            {"id": "fldG9y88Zw7q7u4Z7i4", "name": "Name", "type": "text"},
            {
                "id": "fldB7wkyR0buF1sRF9O",
                "name": "Email",
                "type": "text",
                "typeOptions": {"validatorName": "email"},
            },
            {
                "id": "fldFh5wIL430N62LN6t",
                "name": "Data",
                "type": "foreignKey",
                "typeOptions": {
                    "foreignTableId": "tbl7glLIGtH8C8zGCzb",
                    "symmetricColumnId": "fldQcEaGEe7xuhUEuPL",
                    "relationship": "many",
                    "unreversed": True,
                },
            },
            {
                "id": "fldZBmr4L45mhjILhlA",
                "name": "Number",
                "type": "number",
                "typeOptions": {
                    "format": "integer",
                    "negative": False,
                    "validatorName": "positive",
                },
            },
        ],
    }
    airtable_view = {
        "id": "viwDgBCKTEdCQoHTQKH",
        "name": "Grid",
        "type": "grid",
        "personalForUserId": None,
        "createdByUserId": "usrdGm7k7NIVWhK7W7L",
    }
    airtable_view_data = {
        "id": "viwFSKLuVm97DnNVD91",
        "frozenColumnCount": 1,
        "columnOrder": [
            {"columnId": "fldG9y88Zw7q7u4Z7i4", "visibility": True, "width": 100},
            {"columnId": "fldB7wkyR0buF1sRF9O", "visibility": True},
            {"columnId": "fldZBmr4L45mhjILhlA", "visibility": False},
        ],
        "filters": None,
        "lastSortsApplied": None,
        "groupLevels": None,
        "colorConfig": None,
        "sharesById": {},
        "description": None,
        "createdByUserId": "usrdGm7k7NIVWhK7W7L",
        "applicationTransactionNumber": 284,
        "rowOrder": [
            {"rowId": "recWkle1IOXcLmhILmO", "visibility": True},
            {"rowId": "rec5pdtuKyE71lfK1Ah", "visibility": True},
        ],
    }
    (
        baserow_view,
        airtable_view_type,
    ) = airtable_view_type_registry.from_airtable_view_to_instance(
        table, airtable_view, airtable_view_data, UTC
    )
    assert isinstance(baserow_view, GridView)
    assert isinstance(airtable_view_type, GridAirtableViewType)

    with django_assert_num_queries(0):
        field_options = list(baserow_view.get_field_options())

    assert len(field_options) == 4

    assert field_options[0].grid_view_id == "viwDgBCKTEdCQoHTQKH"
    assert field_options[0].field_id == "fldG9y88Zw7q7u4Z7i4"
    assert field_options[0].hidden is False
    assert field_options[0].width == 100
    assert field_options[0].order == 1

    assert field_options[1].grid_view_id == "viwDgBCKTEdCQoHTQKH"
    assert field_options[1].field_id == "fldB7wkyR0buF1sRF9O"
    assert field_options[1].hidden is False
    assert field_options[1].width == 200
    assert field_options[1].order == 2

    assert field_options[2].grid_view_id == "viwDgBCKTEdCQoHTQKH"
    assert field_options[2].field_id == "fldFh5wIL430N62LN6t"
    assert field_options[2].hidden is False
    assert field_options[2].width == 200
    assert field_options[2].order == 32767

    assert field_options[3].grid_view_id == "viwDgBCKTEdCQoHTQKH"
    assert field_options[3].field_id == "fldZBmr4L45mhjILhlA"
    assert field_options[3].hidden is True
    assert field_options[3].width == 200
    assert field_options[3].order == 3

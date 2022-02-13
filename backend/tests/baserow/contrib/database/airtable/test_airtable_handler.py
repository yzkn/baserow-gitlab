import os
import pytest
import responses
import json

from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from pytz import UTC, timezone as pytz_timezone

from django.core.files.storage import FileSystemStorage
from django.conf import settings

from baserow.core.user_files.models import UserFile
from baserow.core.utils import Progress
from baserow.contrib.database.fields.models import TextField
from baserow.contrib.database.views.models import GridView
from baserow.contrib.database.views.view_types import GridViewType
from baserow.contrib.database.airtable.handler import AirtableHandler
from baserow.contrib.database.airtable.airtable_view_types import GridAirtableViewType


@pytest.mark.django_db
@responses.activate
def test_fetch_publicly_shared_base():
    base_path = os.path.join(settings.BASE_DIR, "../../../tests/airtable_responses")
    path = os.path.join(base_path, "airtable_base.html")

    with open(path, "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/shrXxmp0WmqsTkFWTzv",
            status=200,
            body=file,
            headers={"Set-Cookie": "brw=test;"},
        )

        request_id, init_data, cookies = AirtableHandler.fetch_publicly_shared_base(
            "shrXxmp0WmqsTkFWTzv"
        )
        assert request_id == "req8wbZoh7Be65osz"
        assert init_data["pageLoadId"] == "pglUrFAGTNpbxUymM"
        assert cookies["brw"] == "test"


@pytest.mark.django_db
@responses.activate
def test_fetch_table():
    base_path = os.path.join(settings.BASE_DIR, "../../../tests/airtable_responses")
    path = os.path.join(base_path, "airtable_base.html")
    application_response_path = os.path.join(base_path, "airtable_application.json")
    table_response_path = os.path.join(base_path, "airtable_table.json")

    with open(path, "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/shrXxmp0WmqsTkFWTzv",
            status=200,
            body=file,
            headers={"Set-Cookie": "brw=test;"},
        )
        request_id, init_data, cookies = AirtableHandler.fetch_publicly_shared_base(
            "shrXxmp0WmqsTkFWTzv"
        )

    cookies = {
        "brw": "brw",
        "__Host-airtable-session": "__Host-airtable-session",
        "__Host-airtable-session.sig": "__Host-airtable-session.sig",
        "AWSELB": "AWSELB",
        "AWSELBCORS": "AWSELBCORS",
    }

    with open(application_response_path, "rb") as application_response_file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/application/appZkaH3aWX3ZjT3b/read",
            status=200,
            body=application_response_file,
        )
        application_response = AirtableHandler.fetch_table_data(
            "tblRpq315qnnIcg5IjI",
            init_data,
            request_id,
            cookies,
            fetch_application_structure=True,
            stream=False,
        )

    with open(table_response_path, "rb") as table_response_file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/table/tbl7glLIGtH8C8zGCzb/readData",
            status=200,
            body=table_response_file,
        )
        table_response = AirtableHandler.fetch_table_data(
            "tbl7glLIGtH8C8zGCzb",
            init_data,
            request_id,
            cookies,
            fetch_application_structure=False,
            stream=False,
        )

    assert (
        application_response.json()["data"]["tableSchemas"][0]["id"]
        == "tblRpq315qnnIcg5IjI"
    )
    assert table_response.json()["data"]["id"] == "tbl7glLIGtH8C8zGCzb"


@pytest.mark.django_db
@responses.activate
def test_fetch_view():
    base_path = os.path.join(settings.BASE_DIR, "../../../tests/airtable_responses")
    path = os.path.join(base_path, "airtable_base.html")
    view_response_path = os.path.join(base_path, "airtable_table.json")

    with open(path, "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/shrXxmp0WmqsTkFWTzv",
            status=200,
            body=file,
            headers={"Set-Cookie": "brw=test;"},
        )
        request_id, init_data, cookies = AirtableHandler.fetch_publicly_shared_base(
            "shrXxmp0WmqsTkFWTzv"
        )

    cookies = {
        "brw": "brw",
        "__Host-airtable-session": "__Host-airtable-session",
        "__Host-airtable-session.sig": "__Host-airtable-session.sig",
        "AWSELB": "AWSELB",
        "AWSELBCORS": "AWSELBCORS",
    }

    with open(view_response_path, "rb") as table_response_file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/view/viwDgBCKTEdCQoHTQKH/readData",
            status=200,
            body=table_response_file,
        )
        view_response = AirtableHandler.fetch_view_data(
            "viwDgBCKTEdCQoHTQKH",
            init_data,
            request_id,
            cookies,
            stream=False,
        )

    assert view_response.json()["data"]["id"] == "tbl7glLIGtH8C8zGCzb"


@pytest.mark.django_db
@responses.activate
def test_extract_schema():
    base_path = os.path.join(settings.BASE_DIR, "../../../tests/airtable_responses")
    user_table_path = os.path.join(base_path, "airtable_application.json")
    data_table_path = os.path.join(base_path, "airtable_table.json")
    user_table_json = json.loads(Path(user_table_path).read_text())
    data_table_json = json.loads(Path(data_table_path).read_text())

    schema, tables = AirtableHandler.extract_schema([user_table_json, data_table_json])

    assert "tableDatas" not in schema
    assert len(schema["tableSchemas"]) == 2
    assert schema["tableSchemas"][0]["id"] == "tblRpq315qnnIcg5IjI"
    assert schema["tableSchemas"][1]["id"] == "tbl7glLIGtH8C8zGCzb"
    assert tables["tblRpq315qnnIcg5IjI"]["id"] == "tblRpq315qnnIcg5IjI"
    assert tables["tbl7glLIGtH8C8zGCzb"]["id"] == "tbl7glLIGtH8C8zGCzb"


@pytest.mark.django_db
@responses.activate
def test_to_baserow_view(django_assert_num_queries):
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
        "viewOrder": [
            "viwcpYeEpAs6kZspktV",
            "viwDgBCKTEdCQoHTQKH",
            "viwsFAwnvkr98dfv8nm",
            "viwBAGnUgZ6X5Eyg5Wf",
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
        "id": "viwDgBCKTEdCQoHTQKH",
        "frozenColumnCount": 1,
        "columnOrder": [
            {"columnId": "fldG9y88Zw7q7u4Z7i4", "visibility": True, "width": 100},
            {"columnId": "fldB7wkyR0buF1sRF9O", "visibility": True},
            {"columnId": "fldZBmr4L45mhjILhlA", "visibility": False},
        ],
        "filters": None,
        "lastSortsApplied": {
            "sortSet": [
                {
                    "id": "srtjGg4wXAf7HAQwV",
                    "columnId": "fldG9y88Zw7q7u4Z7i4",
                    "ascending": False,
                },
                {
                    "id": "srtjGg4wXAf7HAQwV",
                    "columnId": "fldB7wkyR0buF1sRF9O",
                    "ascending": True,
                },
            ],
            "shouldAutoSort": True,
            "appliedTime": "2022-01-18T16:30:32.583Z",
        },
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
    field_mapping = {
        "fldG9y88Zw7q7u4Z7i4": {},
        "fldB7wkyR0buF1sRF9O": {},
        "fldFh5wIL430N62LN6t": {},
        "fldZBmr4L45mhjILhlA": {},
    }

    grid_view, baserow_view_type, airtable_view_type = AirtableHandler.to_baserow_view(
        table, airtable_view, airtable_view_data, field_mapping, UTC
    )

    assert isinstance(grid_view, GridView)
    assert isinstance(baserow_view_type, GridViewType)
    assert isinstance(airtable_view_type, GridAirtableViewType)

    assert grid_view.name == "Grid"
    assert grid_view.order == 2

    with django_assert_num_queries(0):
        sortings = grid_view.viewsort_set.all()

    assert sortings[0].view_id == "viwDgBCKTEdCQoHTQKH"
    assert sortings[0].field_id == "fldG9y88Zw7q7u4Z7i4"
    assert sortings[0].order == "DESC"
    assert sortings[1].view_id == "viwDgBCKTEdCQoHTQKH"
    assert sortings[1].field_id == "fldB7wkyR0buF1sRF9O"
    assert sortings[1].order == "ASC"


@pytest.mark.django_db
@responses.activate
def test_to_baserow_database_export():
    base_path = os.path.join(settings.BASE_DIR, "../../../tests/airtable_responses")
    path = os.path.join(base_path, "airtable_base.html")
    user_table_path = os.path.join(base_path, "airtable_application.json")
    data_table_path = os.path.join(base_path, "airtable_table.json")
    user_table_json = json.loads(Path(user_table_path).read_text())
    data_table_json = json.loads(Path(data_table_path).read_text())

    with open(os.path.join(base_path, "file-sample.txt"), "rb") as file:
        responses.add(
            responses.GET,
            "https://dl.airtable.com/.attachments/70e50b90fb83997d25e64937979b6b5b/f3f62d23/file-sample.txt",
            status=200,
            body=file.read(),
        )

    with open(os.path.join(base_path, "file-sample_500kB.doc"), "rb") as file:
        responses.add(
            responses.GET,
            "https://dl.airtable.com/.attachments/e93dc201ce27080d9ad9df5775527d09/93e85b28/file-sample_500kB.doc",
            status=200,
            body=file.read(),
        )

    with open(os.path.join(base_path, "file_example_JPG_100kB.jpg"), "rb") as file:
        responses.add(
            responses.GET,
            "https://dl.airtable.com/.attachments/025730a04991a764bb3ace6d524b45e5/bd61798a/file_example_JPG_100kB.jpg",
            status=200,
            body=file.read(),
        )

    with open(path, "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/shrXxmp0WmqsTkFWTzv",
            status=200,
            body=file.read(),
            headers={"Set-Cookie": "brw=test;"},
        )
        request_id, init_data, cookies = AirtableHandler.fetch_publicly_shared_base(
            "shrXxmp0WmqsTkFWTzv"
        )

    schema, tables = AirtableHandler.extract_schema([user_table_json, data_table_json])
    baserow_database_export, files_buffer = AirtableHandler.to_baserow_database_export(
        init_data, schema, tables, pytz_timezone("Europe/Amsterdam")
    )

    with ZipFile(files_buffer, "r", ZIP_DEFLATED, False) as zip_file:
        assert len(zip_file.infolist()) == 3
        assert (
            zip_file.read(
                "70e50b90fb83997d25e64937979b6b5b_f3f62d23_file-sample" ".txt"
            )
            == b"test\n"
        )

    assert baserow_database_export["id"] == 1
    assert baserow_database_export["name"] == "Test"
    assert baserow_database_export["order"] == 1
    assert baserow_database_export["type"] == "database"
    assert len(baserow_database_export["tables"]) == 2

    assert baserow_database_export["tables"][0]["id"] == "tblRpq315qnnIcg5IjI"
    assert baserow_database_export["tables"][0]["name"] == "Users"
    assert baserow_database_export["tables"][0]["order"] == 0
    assert len(baserow_database_export["tables"][0]["fields"]) == 4

    assert baserow_database_export["tables"][1]["id"] == "tbl7glLIGtH8C8zGCzb"
    assert baserow_database_export["tables"][1]["name"] == "Data"
    assert baserow_database_export["tables"][1]["order"] == 1
    assert len(baserow_database_export["tables"][1]["fields"]) == 23

    # We don't have to check all the fields and rows, just a single one, because we have
    # separate tests for mapping the Airtable fields and values to Baserow.
    assert (
        baserow_database_export["tables"][0]["fields"][0]["id"] == "fldG9y88Zw7q7u4Z7i4"
    )
    assert baserow_database_export["tables"][0]["fields"][0] == {
        "type": "text",
        "id": "fldG9y88Zw7q7u4Z7i4",
        "name": "Name",
        "order": 0,
        "primary": True,
        "text_default": "",
    }
    assert baserow_database_export["tables"][0]["fields"][1] == {
        "type": "email",
        "id": "fldB7wkyR0buF1sRF9O",
        "name": "Email",
        "order": 1,
        "primary": False,
    }
    assert len(baserow_database_export["tables"][0]["rows"]) == 2
    assert baserow_database_export["tables"][0]["rows"][0] == {
        "id": 1,
        "order": "1.00000000000000000000",
        "created_on": "2022-01-16T17:59:13+00:00",
        "updated_on": None,
        "field_fldB7wkyR0buF1sRF9O": "bram@email.com",
        "field_fldG9y88Zw7q7u4Z7i4": "Bram 1",
        "field_fldFh5wIL430N62LN6t": [1],
        "field_fldZBmr4L45mhjILhlA": "1",
    }
    assert baserow_database_export["tables"][0]["rows"][1] == {
        "id": 2,
        "order": "2.00000000000000000000",
        "created_on": "2022-01-16T17:59:13+00:00",
        "updated_on": None,
        "field_fldB7wkyR0buF1sRF9O": "bram@test.nl",
        "field_fldG9y88Zw7q7u4Z7i4": "Bram 2",
        "field_fldFh5wIL430N62LN6t": [2, 3, 1],
        "field_fldZBmr4L45mhjILhlA": "2",
    }
    assert (
        baserow_database_export["tables"][1]["rows"][0]["field_fldEB5dp0mNjVZu0VJI"]
        == "2022-01-21T01:00:00+00:00"
    )


@pytest.mark.django_db
@responses.activate
def test_to_baserow_database_export_without_primary_value():
    base_path = os.path.join(settings.BASE_DIR, "../../../tests/airtable_responses")
    path = os.path.join(base_path, "airtable_base.html")
    user_table_path = os.path.join(base_path, "airtable_application.json")
    user_table_json = json.loads(Path(user_table_path).read_text())

    # Remove the data table because we don't need that one.
    del user_table_json["data"]["tableSchemas"][1]
    user_table_json["data"]["tableDatas"][0]["rows"] = []

    # Rename the primary column so that we depend on the fallback in the migrations.
    user_table_json["data"]["tableSchemas"][0][
        "primaryColumnId"
    ] = "fldG9y88Zw7q7u4Z7i4_unknown"

    with open(path, "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/shrXxmp0WmqsTkFWTzv",
            status=200,
            body=file.read(),
            headers={"Set-Cookie": "brw=test;"},
        )
        request_id, init_data, cookies = AirtableHandler.fetch_publicly_shared_base(
            "shrXxmp0WmqsTkFWTzv"
        )

    schema, tables = AirtableHandler.extract_schema(deepcopy([user_table_json]))
    baserow_database_export, files_buffer = AirtableHandler.to_baserow_database_export(
        init_data, schema, tables, UTC
    )
    assert baserow_database_export["tables"][0]["fields"][0]["primary"] is True

    user_table_json["data"]["tableSchemas"][0]["columns"] = []
    schema, tables = AirtableHandler.extract_schema(deepcopy([user_table_json]))
    baserow_database_export, files_buffer = AirtableHandler.to_baserow_database_export(
        init_data, schema, tables, UTC
    )
    assert baserow_database_export["tables"][0]["fields"] == [
        {
            "type": "text",
            "id": "primary_field",
            "name": "Primary field (auto created)",
            "order": 32767,
            "primary": True,
            "text_default": "",
        }
    ]


@pytest.mark.django_db
@responses.activate
def test_import_from_airtable_to_group(data_fixture, tmpdir):
    group = data_fixture.create_group()
    base_path = os.path.join(settings.BASE_DIR, "../../../tests/airtable_responses")
    storage = FileSystemStorage(location=(str(tmpdir)), base_url="http://localhost")

    with open(os.path.join(base_path, "file-sample.txt"), "rb") as file:
        responses.add(
            responses.GET,
            "https://dl.airtable.com/.attachments/70e50b90fb83997d25e64937979b6b5b/f3f62d23/file-sample.txt",
            status=200,
            body=file.read(),
        )

    with open(os.path.join(base_path, "file-sample_500kB.doc"), "rb") as file:
        responses.add(
            responses.GET,
            "https://dl.airtable.com/.attachments/e93dc201ce27080d9ad9df5775527d09/93e85b28/file-sample_500kB.doc",
            status=200,
            body=file.read(),
        )

    with open(os.path.join(base_path, "file_example_JPG_100kB.jpg"), "rb") as file:
        responses.add(
            responses.GET,
            "https://dl.airtable.com/.attachments/025730a04991a764bb3ace6d524b45e5/bd61798a/file_example_JPG_100kB.jpg",
            status=200,
            body=file.read(),
        )

    with open(os.path.join(base_path, "airtable_base.html"), "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/shrXxmp0WmqsTkFWTzv",
            status=200,
            body=file.read(),
            headers={"Set-Cookie": "brw=test;"},
        )

    with open(os.path.join(base_path, "airtable_application.json"), "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/application/appZkaH3aWX3ZjT3b/read",
            status=200,
            body=file.read(),
        )

    with open(os.path.join(base_path, "airtable_table.json"), "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/table/tbl7glLIGtH8C8zGCzb/readData",
            status=200,
            body=file.read(),
        )

    with open(
        os.path.join(base_path, "airtable_view_viwDgBCKTEdCQoHTQKH.json"), "rb"
    ) as file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/view/viwDgBCKTEdCQoHTQKH/readData",
            status=200,
            body=file.read(),
        )

    with open(
        os.path.join(base_path, "airtable_view_viwsFAwnvkr98dfv8nm.json"), "rb"
    ) as file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/view/viwsFAwnvkr98dfv8nm/readData",
            status=200,
            body=file.read(),
        )

    with open(
        os.path.join(base_path, "airtable_view_viwBAGnUgZ6X5Eyg5Wf.json"), "rb"
    ) as file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/view/viwBAGnUgZ6X5Eyg5Wf/readData",
            status=200,
            body=file.read(),
        )

    progress = Progress(1000)
    databases, id_mapping = AirtableHandler.import_from_airtable_to_group(
        group,
        "shrXxmp0WmqsTkFWTzv",
        timezone=UTC,
        storage=storage,
        progress_builder=progress.create_child_builder(represents_progress=1000),
    )

    assert progress.progress == progress.total
    assert UserFile.objects.all().count() == 3
    file_path = tmpdir.join("user_files", UserFile.objects.all()[0].name)
    assert file_path.isfile()
    assert file_path.open().read() == "test\n"

    database = databases[0]

    assert database.name == "Test"
    all_tables = database.table_set.all()
    assert len(all_tables) == 2

    assert all_tables[0].name == "Users"
    assert all_tables[1].name == "Data"

    user_fields = all_tables[0].field_set.all()
    assert len(user_fields) == 4

    assert user_fields[0].name == "Name"
    assert isinstance(user_fields[0].specific, TextField)

    user_model = all_tables[0].get_model(attribute_names=True)
    rows = user_model.objects.all()
    assert rows[0].id == 1
    assert str(rows[0].order) == "1.00000000000000000000"
    assert rows[0].name == "Bram 1"
    assert rows[0].email == "bram@email.com"
    assert str(rows[0].number) == "1"
    assert [r.id for r in rows[0].data.all()] == [1]

    data_model = all_tables[1].get_model(attribute_names=True)
    rows = data_model.objects.all()
    assert rows[0].checkbox is True
    assert rows[1].checkbox is False

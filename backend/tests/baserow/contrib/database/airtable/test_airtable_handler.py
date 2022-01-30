import os
import pytest
import responses
import json

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.files.storage import FileSystemStorage
from django.conf import settings

from baserow.core.user_files.models import UserFile
from baserow.contrib.database.fields.models import TextField
from baserow.contrib.database.airtable.handler import (
    fetch_publicly_shared_base,
    fetch_table_data,
    extract_schema,
    to_baserow_database_export,
    import_from_airtable_to_group,
)


@pytest.mark.django_db
@responses.activate
def test_fetch_publicly_shared_base():
    base_path = os.path.join(settings.BASE_DIR, "../../../tests/airtable_responses")
    path = os.path.join(base_path, "airtable_base.html")

    with open(path, "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/shrxqmpWsTXkmzvF0",
            status=200,
            body=file,
            headers={"Set-Cookie": "brw=test;"},
        )

        request_id, init_data, cookies = fetch_publicly_shared_base("shrxqmpWsTXkmzvF0")
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
            "https://airtable.com/shrxqmpWsTXkmzvF0",
            status=200,
            body=file,
            headers={"Set-Cookie": "brw=test;"},
        )
        request_id, init_data, cookies = fetch_publicly_shared_base("shrxqmpWsTXkmzvF0")

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
            "https://airtable.com/v0.3/application/appEzkH33aWXZtJ4B/read",
            status=200,
            body=application_response_file,
        )
        application_response = fetch_table_data(
            "tblpnq35nIRcqjIg1",
            init_data,
            request_id,
            cookies,
            fetch_application_structure=True,
            stream=False,
        )

    with open(table_response_path, "rb") as table_response_file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/table/tblgHtLG8C78lzbzI/readData",
            status=200,
            body=table_response_file,
        )
        table_response = fetch_table_data(
            "tblgHtLG8C78lzbzI",
            init_data,
            request_id,
            cookies,
            fetch_application_structure=False,
            stream=False,
        )

    assert (
        application_response.json()["data"]["tableSchemas"][0]["id"]
        == "tblpnq35nIRcqjIg1"
    )
    assert table_response.json()["data"]["id"] == "tblgHtLG8C78lzbzI"


@pytest.mark.django_db
@responses.activate
def test_extract_schema():
    base_path = os.path.join(settings.BASE_DIR, "../../../tests/airtable_responses")
    user_table_path = os.path.join(base_path, "airtable_application.json")
    data_table_path = os.path.join(base_path, "airtable_table.json")
    user_table_json = json.loads(Path(user_table_path).read_text())
    data_table_json = json.loads(Path(data_table_path).read_text())

    schema, tables = extract_schema([user_table_json, data_table_json])

    assert "tableDatas" not in schema
    assert len(schema["tableSchemas"]) == 2
    assert schema["tableSchemas"][0]["id"] == "tblpnq35nIRcqjIg1"
    assert schema["tableSchemas"][1]["id"] == "tblgHtLG8C78lzbzI"
    assert tables["tblpnq35nIRcqjIg1"]["id"] == "tblpnq35nIRcqjIg1"
    assert tables["tblgHtLG8C78lzbzI"]["id"] == "tblgHtLG8C78lzbzI"


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
            "https://airtable.com/shrxqmpWsTXkmzvF0",
            status=200,
            body=file.read(),
            headers={"Set-Cookie": "brw=test;"},
        )
        request_id, init_data, cookies = fetch_publicly_shared_base("shrxqmpWsTXkmzvF0")

    schema, tables = extract_schema([user_table_json, data_table_json])
    baserow_database_export, files_buffer = to_baserow_database_export(
        init_data, schema, tables
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

    assert baserow_database_export["tables"][0]["id"] == "tblpnq35nIRcqjIg1"
    assert baserow_database_export["tables"][0]["name"] == "Users"
    assert baserow_database_export["tables"][0]["order"] == 0
    assert len(baserow_database_export["tables"][0]["fields"]) == 4

    assert baserow_database_export["tables"][1]["id"] == "tblgHtLG8C78lzbzI"
    assert baserow_database_export["tables"][1]["name"] == "Data"
    assert baserow_database_export["tables"][1]["order"] == 1
    assert len(baserow_database_export["tables"][1]["fields"]) == 23

    # We don't have to check all the fields and rows, just a single one, because we have
    # separate tests for mapping the Airtable fields and values to Baserow.
    assert (
        baserow_database_export["tables"][0]["fields"][0]["id"] == "fld97w8Zq7Guyi448"
    )
    assert baserow_database_export["tables"][0]["fields"][0] == {
        "type": "text",
        "id": "fld97w8Zq7Guyi448",
        "name": "Name",
        "order": 0,
        "primary": True,
    }
    assert baserow_database_export["tables"][0]["fields"][1] == {
        "type": "email",
        "id": "fld7b0kRuFB1w9Osy",
        "name": "Email",
        "order": 1,
        "primary": False,
    }
    assert len(baserow_database_export["tables"][0]["rows"]) == 2
    assert baserow_database_export["tables"][0]["rows"][0] == {
        "id": 1,
        "order": "1.00000000000000000000",
        "field_fld7b0kRuFB1w9Osy": "bram@email.com",
        "field_fld97w8Zq7Guyi448": "Bram 1",
        "field_fldh34wL0NF656t2I": [1],
        "field_fldB54rLmhZjmlAI4": "1",
    }
    assert baserow_database_export["tables"][0]["rows"][1] == {
        "id": 2,
        "order": "2.00000000000000000000",
        "field_fld7b0kRuFB1w9Osy": "bram@test.nl",
        "field_fld97w8Zq7Guyi448": "Bram 2",
        "field_fldh34wL0NF656t2I": [2, 3, 1],
        "field_fldB54rLmhZjmlAI4": "2",
    }


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
            "https://airtable.com/shrxqmpWsTXkmzvF0",
            status=200,
            body=file.read(),
            headers={"Set-Cookie": "brw=test;"},
        )

    with open(os.path.join(base_path, "airtable_application.json"), "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/application/appEzkH33aWXZtJ4B/read",
            status=200,
            body=file.read(),
        )

    with open(os.path.join(base_path, "airtable_table.json"), "rb") as file:
        responses.add(
            responses.GET,
            "https://airtable.com/v0.3/table/tblgHtLG8C78lzbzI/readData",
            status=200,
            body=file.read(),
        )

    databases, id_mapping = import_from_airtable_to_group(
        group, "shrxqmpWsTXkmzvF0", storage=storage
    )

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

import re
import json
import requests
from collections import defaultdict
from typing import List, Tuple
from requests import Response
from io import BytesIO, IOBase
from zipfile import ZipFile, ZIP_DEFLATED

from baserow.core.handler import CoreHandler
from baserow.core.utils import Progress
from baserow.contrib.database.application_types import DatabaseApplicationType
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.airtable.constants import (
    AIRTABLE_EXPORT_JOB_DOWNLOADING_STRUCTURE,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES,
    AIRTABLE_EXPORT_JOB_CONVERTING,
)


BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def fetch_publicly_shared_base(share_id: str) -> Tuple[str, dict, dict]:
    """
    Fetches the initial page of the publicly shared page. It will parse the content
    and extract and return the initial data needed for future requests.

    :param share_id: The Airtable share id of the page that must be fetched. Note
        that the base must be shared publicly. The id stars with `shr`.
    :return: The request ID, initial data and the cookies of the response.
    """

    url = f"https://airtable.com/{share_id}"
    response = requests.get(url, headers=BASE_HEADERS)
    content = response.content
    decoded_content = content.decode()

    request_id = re.search('requestId: "(.*)",', decoded_content).group(1)
    raw_init_data = re.search("window.initData = (.*);\n", decoded_content).group(1)
    init_data = json.loads(raw_init_data)
    cookies = response.cookies.get_dict()

    return request_id, init_data, cookies


def fetch_table_data(
    table_id: str,
    init_data: dict,
    request_id: str,
    cookies: dict,
    fetch_application_structure: bool,
    stream=True,
) -> Response:
    """
    Fetches the data or application structure of a publicly shared Airtable table.

    :param table_id: The Airtable table id that must be fetched. The id starts with
        `tbl`.
    :param init_data: The init_data returned by the initially requested shared base.
    :param request_id: The request_id returned by the initially requested shared base.
    :param cookies: The cookies dict returned by the initially requested shared base.
    :param fetch_application_structure: Indicates whether the application structure
        must also be fetched.
        If True, the schema of all the tables and views will be included in the
        response. Note that the structure of the response is different because it
        will wrap application/table schema around the table data. The table data will
        be available at the path `data.tableDatas.0.rows`.
        If False, the only the table data will be included in the response JSON,
        which will be available at the path `data.rows`.
    :param stream: Indicates whether the request should be streamed. This could be
        useful if we want to show a progress bar. It will directly be passed into the
        `requests` request.
    :return: The `requests` response containing the result.
    """

    application_id = list(init_data["rawApplications"].keys())[0]
    client_code_version = init_data["codeVersion"]
    page_load_id = init_data["pageLoadId"]

    stringified_object_params = {
        "includeDataForViewIds": None,
        "shouldIncludeSchemaChecksum": True,
        "mayOnlyIncludeRowAndCellDataForIncludedViews": True,
    }
    access_policy = json.loads(init_data["accessPolicy"])

    if fetch_application_structure:
        stringified_object_params["includeDataForTableIds"] = [table_id]
        url = f"https://airtable.com/v0.3/application/{application_id}/read"
    else:
        url = f"https://airtable.com/v0.3/table/{table_id}/readData"

    response = requests.get(
        url=url,
        stream=stream,
        params={
            "stringifiedObjectParams": json.dumps(stringified_object_params),
            "requestId": request_id,
            "accessPolicy": json.dumps(access_policy),
        },
        headers={
            "x-airtable-application-id": application_id,
            "x-airtable-client-queue-time": "45",
            "x-airtable-inter-service-client": "webClient",
            "x-airtable-inter-service-client-code-version": client_code_version,
            "x-airtable-page-load-id": page_load_id,
            "X-Requested-With": "XMLHttpRequest",
            "x-time-zone": "Europe/Amsterdam",
            "x-user-locale": "en",
            **BASE_HEADERS,
        },
        cookies=cookies,
    )
    return response


def extract_schema(exports: List[dict]) -> Tuple[dict, dict]:
    """
    Loops over the provided exports and finds the export containing the application
    schema. That will be extracted and the rest of the table data will be moved
    into a dict where the key is the table id.

    :param exports: A list containing all the exports as dicts.
    :return: The database schema and a dict containing the table data.
    """

    schema = None
    tables = {}

    for export in exports:
        if "appBlanket" in export["data"]:
            table_data = export["data"].pop("tableDatas")[0]
            schema = export["data"]
        else:
            table_data = export["data"]

        tables[table_data["id"]] = table_data

    if schema is None:
        raise ValueError("None of the provided exports contains the schema.")

    return schema, tables


def to_baserow_field_export(table: dict, column: dict):
    exported_field, field_type = field_type_registry.from_airtable_field_to_serialized(
        column
    )

    if exported_field is None:
        return None, None

    order = next(
        index
        for index, value in enumerate(table["meaningfulColumnOrder"])
        if value["columnId"] == column["id"]
    )

    exported_field.update(
        **{
            "id": column["id"],
            "name": column["name"],
            "order": order,
            "primary": table["primaryColumnId"] == column["id"],
        }
    )
    return exported_field, field_type


def to_baserow_row_export(
    row_id_mapping, column_mapping, row, index, files_to_download
):
    exported_row = {
        "id": row["id"],
        "order": f"{index + 1}.00000000000000000000",
    }

    for column_id, column_value in row["cellValuesByColumnId"].items():
        if column_id not in column_mapping:
            continue

        field_value = column_mapping[column_id]
        value = field_value[
            "baserow_field_type"
        ].from_airtable_column_value_to_serialized(
            row_id_mapping,
            field_value["airtable_field"],
            field_value["baserow_field"],
            column_value,
            files_to_download,
        )
        exported_row[f"field_{column_id}"] = value

    return exported_row


def download_files_as_zip(files_to_download, parent_progress=None):
    files_buffer = BytesIO()
    total = len(files_to_download.keys())
    progress = Progress(total)

    if parent_progress:
        parent_progress[0].add_child(progress, parent_progress[1])

    with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
        for index, (file_name, url) in enumerate(files_to_download.items()):
            response = requests.get(url, headers=BASE_HEADERS)
            files_zip.writestr(file_name, response.content)
            progress.increment(AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES)

    return files_buffer


def to_baserow_database_export(
    init_data: dict,
    schema: dict,
    tables: dict,
    parent_progress=None,
) -> Tuple[dict, IOBase]:
    """

    :param init_data:
    :param schema:
    :param tables:
    :param parent_progress:
    :return:
    """

    progress = Progress(100)

    if parent_progress:
        parent_progress[0].add_child(progress, parent_progress[1])

    exported_tables = []
    files_to_download = {}
    row_id_mapping = defaultdict(dict)

    # @TODO explain why we need a mapping
    mapping_progress = Progress(len(schema["tableSchemas"]))
    progress.add_child(mapping_progress, 10)
    for index, table in enumerate(schema["tableSchemas"]):
        for row_index, row in enumerate(tables[table["id"]]["rows"]):
            new_id = row_index + 1
            row_id_mapping[table["id"]][row["id"]] = new_id
            row["id"] = new_id
        mapping_progress.increment(AIRTABLE_EXPORT_JOB_CONVERTING)

    table_progress = Progress(len(schema["tableSchemas"]) * 120)
    progress.add_child(table_progress, 60)
    for table_index, table in enumerate(schema["tableSchemas"]):
        field_mapping = {}

        column_progress = Progress(len(table["columns"]))
        table_progress.add_child(column_progress, 19)
        for column in table["columns"]:
            field_export, field_type = to_baserow_field_export(table, column)

            # None means that none of the field types know how to parse this field,
            # so we must ignore it.
            if field_export is None:
                continue

            field_mapping[column["id"]] = {
                "airtable_field": column,
                "baserow_field": field_export,
                "baserow_field_type": field_type,
            }
            column_progress.increment(AIRTABLE_EXPORT_JOB_CONVERTING)

        rows_progress = Progress(len(tables[table["id"]]["rows"]))
        table_progress.add_child(rows_progress, 100)
        exported_rows = []
        for row_index, row in enumerate(tables[table["id"]]["rows"]):
            exported_rows.append(
                to_baserow_row_export(
                    row_id_mapping,
                    field_mapping,
                    row,
                    row_index,
                    files_to_download,
                )
            )
            rows_progress.increment(AIRTABLE_EXPORT_JOB_CONVERTING)

        exported_table = {
            "id": table["id"],
            "name": table["name"],
            "order": table_index,
            "fields": [value["baserow_field"] for value in field_mapping.values()],
            "views": [],
            "rows": exported_rows,
        }
        exported_tables.append(exported_table)
        table_progress.increment(AIRTABLE_EXPORT_JOB_CONVERTING)

    exported_database = {
        "id": 1,
        "name": init_data["rawApplications"][init_data["sharedApplicationId"]]["name"],
        "order": 1,
        "type": DatabaseApplicationType.type,
        "tables": exported_tables,
    }

    user_files_zip = download_files_as_zip(files_to_download, (progress, 30))

    return exported_database, user_files_zip


def import_from_airtable_to_group(group, share_id, storage=None, parent_progress=None):
    progress = Progress(100)

    if parent_progress:
        parent_progress[0].add_child(progress, parent_progress[1])

    request_id, init_data, cookies = fetch_publicly_shared_base(share_id)
    progress.increment(AIRTABLE_EXPORT_JOB_DOWNLOADING_STRUCTURE)

    tables = []
    raw_tables = list(init_data["rawTables"].keys())
    table_progress = Progress(len(raw_tables))
    progress.add_child(table_progress, 19)
    for index, table_id in enumerate(raw_tables):
        tables.append(
            fetch_table_data(
                table_id=table_id,
                init_data=init_data,
                request_id=request_id,
                cookies=cookies,
                fetch_application_structure=index == 0,
                stream=False,
            ).json()
        )
        table_progress.increment(AIRTABLE_EXPORT_JOB_DOWNLOADING_STRUCTURE)

    schema, tables = extract_schema(tables)
    baserow_database_export, files_buffer = to_baserow_database_export(
        init_data, schema, tables, (progress, 40)
    )

    databases, id_mapping = CoreHandler().import_applications_to_group(
        group,
        [baserow_database_export],
        files_buffer,
        storage=storage,
        parent_progress=(progress, 40),
    )

    return databases, id_mapping

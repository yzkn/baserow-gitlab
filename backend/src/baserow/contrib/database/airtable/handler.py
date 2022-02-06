import re
import json
import requests
from collections import defaultdict
from typing import List, Tuple, Union, Dict, Optional
from requests import Response
from io import BytesIO, IOBase
from zipfile import ZipFile, ZIP_DEFLATED

from django.core.files.storage import Storage

from baserow.core.handler import CoreHandler
from baserow.core.utils import Progress, remove_invalid_surrogate_characters
from baserow.core.models import Group
from baserow.contrib.database.models import Database
from baserow.contrib.database.fields.registries import FieldType
from baserow.contrib.database.application_types import DatabaseApplicationType
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.airtable.constants import (
    AIRTABLE_EXPORT_JOB_DOWNLOADING_BASE,
    AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES,
    AIRTABLE_EXPORT_JOB_CONVERTING,
)

from .exceptions import AirtableBaseNotPublic


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

    if not response.ok:
        raise AirtableBaseNotPublic(f"The base with share id {share_id} is not public.")

    decoded_content = remove_invalid_surrogate_characters(response.content)

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
        must also be fetched. If True, the schema of all the tables and views will be
        included in the response. Note that the structure of the response is
        different because it will wrap application/table schema around the table
        data. The table data will be available at the path `data.tableDatas.0.rows`.
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


def to_baserow_field_export(
    table: dict, column: dict
) -> Tuple[Union[dict, None], Union[FieldType, None]]:
    """
    Converts the provided Airtable column dict to Baserow export field format.

    :param table: The Airtable table dict. This is needed to figure out whether the
        field is the primary field.
    :param column: The Airtable column dict. These values will be converted to
        Baserow format.
    :return: The converted column as a Baserow field export.
    """

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
    row_id_mapping: Dict[str, Dict[str, int]],
    column_mapping: Dict[str, dict],
    row: dict,
    index: int,
    files_to_download: Dict[str, str],
) -> dict:
    """
    Converts the provided Airtable record to a Baserow row by looping over the field
    types and executing the `from_airtable_column_value_to_serialized` method.

    :param row_id_mapping: A mapping containing the table as key as the value is
        another mapping where the Airtable row id maps the Baserow row id.
    :param column_mapping: A mapping where the Airtable colum id is the value and the
        value containing another mapping with the Airtable column dict and Baserow
        field dict.
    :param row: The Airtable row that must be converted a Baserow row.
    :param index: The index the row has in the table.
    :param files_to_download: A dict that contains all the user file URLs that must be
        downloaded. The key is the file name and the value the URL. Additional files
        can be added to this dict.
    :return: The converted row in Baserow export format.
    """

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


def download_files_as_zip(
    files_to_download: Dict[str, str],
    parent_progress: Optional[Tuple[Progress, int]] = None,
) -> BytesIO:
    """
    Downloads all the user files in the provided dict and adds them to a zip file.
    The key of the dict will be the file name in the zip file.

    :param files_to_download: A dict that contains all the user file URLs that must be
        downloaded. The key is the file name and the value the URL. Additional files
        can be added to this dict.
    :param parent_progress: If provided, the progress will be registered as child to
        the `parent_progress`.
    :return: An in memory buffer as zip file containing all the user files.
    """

    files_buffer = BytesIO()
    progress = Progress(len(files_to_download.keys()))

    if parent_progress:
        parent_progress[0].add_child(progress, parent_progress[1])

    with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
        for index, (file_name, url) in enumerate(files_to_download.items()):
            response = requests.get(url, headers=BASE_HEADERS)
            files_zip.writestr(file_name, response.content)
            progress.increment(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_FILES)

    return files_buffer


def to_baserow_database_export(
    init_data: dict,
    schema: dict,
    tables: list,
    parent_progress: Optional[Tuple[Progress, int]] = None,
) -> Tuple[dict, IOBase]:
    """
    Converts the provided raw Airtable database dict to a Baserow export format and
    an in memory zip file containing all the downloaded user files.

    @TODO add the views.
    @TODO preserve the order of least one view.
    @TODO fall back on another field if the primary field is not supported.

    :param init_data: The init_data, extracted from the initial page related to the
        shared base.
    :param schema: An object containing the schema of the Airtable base.
    :param tables: a list containing the table data.
    :param parent_progress: If provided, the progress will be registered as child to
        the `parent_progress`.
    :return: The converted Airtable base in Baserow export format and a zip file
        containing the user files.
    """

    progress = Progress(1000)
    converting_progress = Progress(
        sum(
            [
                # Mapping progress
                len(tables[table["id"]]["rows"])
                # Table column progress
                + len(table["columns"])
                # Table rows progress
                + len(tables[table["id"]]["rows"])
                # The table itself.
                + 1
                for table in schema["tableSchemas"]
            ]
        )
    )
    progress.add_child(converting_progress, 500)

    if parent_progress:
        parent_progress[0].add_child(progress, parent_progress[1])

    # A list containing all the exported table in Baserow format.
    exported_tables = []

    # A dict containing all the user files that must be downloaded and added to a zip
    # file.
    files_to_download = {}

    # A mapping containing the Airtable table id as key and as value another mapping
    # containing with the key as Airtable row id and the value as new Baserow row id.
    # This mapping is created because Airtable has string row id that look like
    # "recAjnk3nkj5", but Baserow doesn't support string row id, so we need to
    # replace them with a unique int. We need a mapping because there could be
    # references to the row.
    row_id_mapping = defaultdict(dict)
    for index, table in enumerate(schema["tableSchemas"]):
        for row_index, row in enumerate(tables[table["id"]]["rows"]):
            new_id = row_index + 1
            row_id_mapping[table["id"]][row["id"]] = new_id
            row["id"] = new_id
            converting_progress.increment(state=AIRTABLE_EXPORT_JOB_CONVERTING)

    for table_index, table in enumerate(schema["tableSchemas"]):
        field_mapping = {}

        # Loop over all the columns in the table and try to convert them to Baserow
        # format.
        for column in table["columns"]:
            field_export, field_type = to_baserow_field_export(table, column)

            # None means that none of the field types know how to parse this field,
            # so we must ignore it.
            if field_export is None:
                continue

            # Construct a mapping where the Airtable column id is the key and the
            # value contains the row Airtable field values, Baserow field values and
            # the Baserow field type object for later use.
            field_mapping[column["id"]] = {
                "airtable_field": column,
                "baserow_field": field_export,
                "baserow_field_type": field_type,
            }
            converting_progress.increment(state=AIRTABLE_EXPORT_JOB_CONVERTING)

        # Loop over all the rows in the table and convert them to Baserow format. We
        # need to provide the `row_id_mapping` and `field_mapping` because there
        # could be references to other rows and fields. the `files_to_download` is
        # needed because every value could be depending on additional files that must
        # later be downloaded.
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
            converting_progress.increment(state=AIRTABLE_EXPORT_JOB_CONVERTING)

        exported_table = {
            "id": table["id"],
            "name": table["name"],
            "order": table_index,
            "fields": [value["baserow_field"] for value in field_mapping.values()],
            "views": [],
            "rows": exported_rows,
        }
        exported_tables.append(exported_table)
        converting_progress.increment(state=AIRTABLE_EXPORT_JOB_CONVERTING)

    exported_database = {
        "id": 1,
        "name": init_data["rawApplications"][init_data["sharedApplicationId"]]["name"],
        "order": 1,
        "type": DatabaseApplicationType.type,
        "tables": exported_tables,
    }

    # After all the tables have been converted to Baserow format, we can must
    # download all the user files. Because we first want to the whole conversion to
    # be completed and because we want this to be added to the progress bar, this is
    # done last.
    user_files_zip = download_files_as_zip(files_to_download, (progress, 500))

    return exported_database, user_files_zip


def import_from_airtable_to_group(
    group: Group,
    share_id: str,
    storage: Optional[Storage] = None,
    parent_progress: Optional[Tuple[Progress, int]] = None,
) -> Tuple[List[Database], dict]:
    """
    Downloads all the data of the provided publicly shared Airtable base, converts it
    into Baserow export format, downloads the related files and imports that converted
    base into the provided group.

    :param group: The group where the copy of the Airtable must be added to.
    :param share_id: The shared Airtable ID that must be imported.
    :param storage: The storage where the user files must be saved to.
    :param parent_progress: If provided, the progress will be registered as child to
        the `parent_progress`.
    :return:
    """

    progress = Progress(1000)

    if parent_progress:
        parent_progress[0].add_child(progress, parent_progress[1])

    # Execute the initial request to obtain the initial data that's needed to make the
    request_id, init_data, cookies = fetch_publicly_shared_base(share_id)
    progress.increment(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_BASE)

    # Loop over all the tables and make a request for each table to obtain the raw
    # Airtable table data.
    tables = []
    raw_tables = list(init_data["rawTables"].keys())
    table_progress = Progress(len(raw_tables))
    progress.add_child(table_progress, 99)
    for index, table_id in enumerate(raw_tables):
        response = fetch_table_data(
            table_id=table_id,
            init_data=init_data,
            request_id=request_id,
            cookies=cookies,
            # At least one request must also fetch the application structure that
            # contains the schema of all the tables, so we do this for the first table.
            fetch_application_structure=index == 0,
            stream=False,
        )
        decoded_content = remove_invalid_surrogate_characters(response.content)
        tables.append(json.loads(decoded_content))
        table_progress.increment(state=AIRTABLE_EXPORT_JOB_DOWNLOADING_BASE)

    # Split database schema from the tables because we need this to be separated
    # later on..
    schema, tables = extract_schema(tables)

    # Convert the raw Airtable data to Baserow export format so we can import that
    # later.
    baserow_database_export, files_buffer = to_baserow_database_export(
        init_data, schema, tables, (progress, 300)
    )

    # Import the converted data using the existing method to avoid duplicate code.
    databases, id_mapping = CoreHandler().import_applications_to_group(
        group,
        [baserow_database_export],
        files_buffer,
        storage=storage,
        parent_progress=(progress, 600),
    )

    return databases, id_mapping

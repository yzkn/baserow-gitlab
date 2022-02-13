from typing import Dict, Any, Union, Tuple

from pytz import BaseTzInfo

from baserow.core.registry import Instance, Registry
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.views.models import View


class AirtableColumnType(Instance):
    def to_baserow_field(
        self, raw_airtable_column: dict, timezone: BaseTzInfo
    ) -> Union[Field, None]:
        """
        Converts the raw Airtable column to a Baserow field object. It should be
        possible to pass this object directly into the FieldType::export_serialized
        method to convert it to the Baserow export format.

        :param raw_airtable_column: The raw Airtable column values that must be
            converted.
        :param timezone: The main timezone used for date conversions if needed.
        :return: The Baserow field type relatd to the Airtable column. If None is
            provided, then the column is ignored in the conversion.
        """

        raise NotImplementedError("The `to_baserow_field` must be implemented.")

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping: Dict[str, Dict[str, int]],
        raw_airtable_column: dict,
        baserow_field: Field,
        value: Any,
        timezone: BaseTzInfo,
        files_to_download: Dict[str, str],
    ):
        """
        This method should convert a raw Airtable row value to a Baserow export row
        value. This method is only called if the Airtable field is compatible with a
        Baserow field type, this is determined by the
        `from_airtable_field_to_serialized` method.

        :param row_id_mapping: A mapping containing the table as key as the value is
            another mapping where the Airtable row id maps the Baserow row id.
        :param raw_airtable_column: A dict containing the raw Airtable column values.
        :param baserow_field: The Baserow field that the column has been converted to.
        :param value: The raw Airtable value that must be converted.
        :param timezone: The main timezone used for date conversions if needed.
        :param files_to_download: A dict that contains all the user file URLs that must
            be downloaded. The key is the file name and the value the URL. Additional
            files can be added to this dict.
        :return: The converted value is Baserow export format.
        """

        return value


class AirtableColumnTypeRegistry(Registry):
    name = "airtable_column"

    def from_airtable_column_to_serialized(
        self, raw_airtable_column: dict, timezone: BaseTzInfo
    ) -> Union[Tuple[Field, AirtableColumnType], Tuple[None, None]]:
        """
        Tries to find a Baserow field that matches that raw Airtable column data. If
        None is returned, the column is not compatible with Baserow and must be ignored.

        :param raw_airtable_column: The raw Airtable column data that must be
        :param timezone: The main timezone used for date conversions if needed.
        :return: The related Baserow field and AirtableColumnType that should be used
            for the conversion.
        """

        try:
            type_name = raw_airtable_column.get("type", "")
            airtable_column_type = self.get(type_name)
            baserow_field = airtable_column_type.to_baserow_field(
                raw_airtable_column, timezone
            )

            if baserow_field is None:
                return None, None
            else:
                return baserow_field, airtable_column_type
        except self.does_not_exist_exception_class:
            return None, None


class AirtableViewType(Instance):
    def to_baserow_view(
        self,
        table: dict,
        raw_airtable_view: dict,
        raw_airtable_view_data: dict,
        field_mapping: dict,
        timezone: BaseTzInfo,
    ) -> Union[View, None]:
        """
        @TODO docs

        :param table: @TODO
        :param raw_airtable_view:
        :param raw_airtable_view_data:
        :param field_mapping: @TODO
        :param timezone:
        :return:
        """

        raise NotImplementedError("The `to_baserow_field` must be implemented.")


class AirtableViewTypeRegistry(Registry):
    name = "airtable_view"

    def from_airtable_view_to_instance(
        self,
        table: dict,
        raw_airtable_view: dict,
        raw_airtable_view_data: dict,
        field_mapping: dict,
        timezone: BaseTzInfo,
    ) -> Union[Tuple[Field, AirtableColumnType], Tuple[None, None]]:
        """
        @TODO

        :param table: @TODO
        :param raw_airtable_view: @TODO
        :param raw_airtable_view_data: @TODO
        :param field_mapping: @TODO
        :param timezone: The main timezone used for date conversions if needed.
        :return: The related Baserow view and AirtableViewType.
        """

        try:
            type_name = raw_airtable_view.get("type", "")
            airtable_view_type = self.get(type_name)
            baserow_view = airtable_view_type.to_baserow_view(
                table,
                raw_airtable_view,
                raw_airtable_view_data,
                field_mapping,
                timezone,
            )

            if baserow_view is None:
                return None, None
            else:
                return baserow_view, airtable_view_type
        except self.does_not_exist_exception_class:
            return None, None


# A default view type registry is created here, this is the one that is used
# throughout the whole Baserow application to add a new view type.
airtable_column_type_registry = AirtableColumnTypeRegistry()
airtable_view_type_registry = AirtableViewTypeRegistry()

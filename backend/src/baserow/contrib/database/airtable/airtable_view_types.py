from baserow.contrib.database.views.models import GridView, GridViewFieldOptions

from .registry import AirtableViewType


class GridAirtableViewType(AirtableViewType):
    type = "grid"

    def to_baserow_view(
        self,
        table,
        raw_airtable_view,
        raw_airtable_view_data,
        field_mapping,
        timezone,
    ):
        field_options = []
        for column in table["columns"]:
            # If the column is not in the field mapping, it means that the field has
            # not been added because it's not compatible with Baserow.
            if column["id"] not in field_mapping:
                continue

            column_order = {}
            column_index = None

            try:
                column_index, column_order = next(
                    (index, value)
                    for index, value in enumerate(raw_airtable_view_data["columnOrder"])
                    if value["columnId"] == column["id"]
                )
            except StopIteration:
                pass

            kwargs = {}

            if "visibility" in column_order:
                kwargs["hidden"] = not column_order["visibility"]

            if "width" in column_order:
                kwargs["width"] = column_order["width"]

            if column_index is not None:
                kwargs["order"] = column_index + 1

            field_options.append(
                GridViewFieldOptions(
                    grid_view_id=raw_airtable_view["id"],
                    field_id=column["id"],
                    **kwargs
                )
            )

        view = GridView()
        # The grid view `export_serialized` uses the `get_field_options` to fetch the
        # related field options. Overriding them means that our field options are
        # going to be included in the export.
        view.get_field_options = lambda *args, **kwargs: field_options
        return view

from .constants import AIRTABLE_BASEROW_COLOR_MAPPING


def import_airtable_date_type_options(type_options):
    date_format_mapping = {"European": "EU", "US": "US"}
    time_format_mapping = {"12hour": "12", "24hour": "24"}
    return {
        "date_format": date_format_mapping.get(type_options.get("dateFormat"), "ISO"),
        "date_include_time": type_options.get("isDateTime", False),
        "date_time_format": time_format_mapping.get(
            type_options.get("timeFormat"), "24"
        ),
    }


def import_airtable_choices(type_options):
    order = type_options.get("choiceOrder", [])
    choices = type_options.get("choices", [])
    return [
        {
            "id": choice["id"],
            "value": choice["name"],
            "color": AIRTABLE_BASEROW_COLOR_MAPPING.get(choice["color"], "blue"),
            "order": order.index(choice["id"]),
        }
        for choice in choices.values()
    ]

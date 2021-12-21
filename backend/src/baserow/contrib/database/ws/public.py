from typing import Dict, Any, Type, Optional, List, Callable

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.models import GeneratedTableModel, Table
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View
from baserow.ws.registries import page_registry


def find_public_views_row_is_in(table, model, row):
    view_slugs = []
    view_handler = ViewHandler()
    for view in table.view_set.filter(public=True).all():
        if view_handler.apply_filters(view, model.objects.filter(id=row.id)).exists():
            view_slugs.append(view.slug)
    return view_slugs


def find_public_views_field_is_in(field):
    view_slugs = []
    view_handler = ViewHandler()
    from baserow.contrib.database.views.registries import view_type_registry

    for view in field.table.view_set.filter(public=True).all():
        view_type = view_type_registry.get_by_model(view.specific_class)
        if view_type.includes_field(view, field):
            view_slugs.append(view.slug)
    return view_slugs


def broadcast_event_to_a_tables_public_views(
    table: Table,
    event_data: Dict[str, Any],
    model: Optional[Type[GeneratedTableModel]] = None,
    row: Optional[GeneratedTableModel] = None,
    field: Optional[Field] = None,
    view_slugs: Optional[List[str]] = None,
    must_send: Optional[List[int]] = None,
    must_send_mutator: Callable[[Dict[str, Any], str], type(None)] = None,
):
    view_handler = ViewHandler()
    public_view_page_table = page_registry.get("view")

    event_data.pop("table_id", None)
    event_data.pop("database_id", None)
    if "metadata" in event_data:
        event_data["metadata"] = {}

    if view_slugs is None:
        views = table.view_set.filter(public=True).all()
    else:
        views = table.view_set.filter(slug__in=view_slugs, public=True)

    if must_send is None:
        must_send = set()
    else:
        must_send = set(must_send)
    print(must_send)
    for view in views:
        event_data["view_slug"] = view.slug
        broadcast = True
        if row is not None and model is not None:
            broadcast = (
                broadcast
                and view_handler.apply_filters(
                    view, model.objects.filter(id=row.id)
                ).exists()
            )
        if field is not None:
            from baserow.contrib.database.views.registries import view_type_registry

            view_type = view_type_registry.get_by_model(view.specific_class)
            broadcast = broadcast and view_type.includes_field(view, field)

        if broadcast:
            if view.slug in must_send:
                must_send.remove(view.slug)
            elif must_send_mutator is not None:
                must_send_mutator(event_data, "created")
            public_view_page_table.broadcast(event_data, None, slug=view.slug)
    for view_slug in must_send:
        if must_send_mutator is not None:
            must_send_mutator(event_data, "deleted")
        public_view_page_table.broadcast(event_data, None, slug=view_slug)


def broadcast_event_to_view_if_public(view: View, event_data: Dict[str, Any]):
    if view.public:
        event_data["view_slug"] = view.slug
        public_view_page_table = page_registry.get("view")
        public_view_page_table.broadcast(event_data, None, slug=view.slug)

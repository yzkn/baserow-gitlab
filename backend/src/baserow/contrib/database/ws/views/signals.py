from django.dispatch import receiver
from django.db import transaction

from baserow.contrib.database.api.fields.serializers import FieldSerializer
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.ws.public import (
    broadcast_event_to_view_if_public,
)
from baserow.ws.registries import page_registry

from baserow.contrib.database.views import signals as view_signals
from baserow.contrib.database.views.registries import view_type_registry
from baserow.contrib.database.api.views.serializers import (
    ViewSerializer,
    ViewFilterSerializer,
    ViewSortSerializer,
)


@receiver(view_signals.view_created)
def view_created(sender, view, user, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "view_created",
                "view": view_type_registry.get_serializer(
                    view,
                    ViewSerializer,
                    filters=True,
                    sortings=True,
                ).data,
            },
            getattr(user, "web_socket_id", None),
            table_id=view.table_id,
        )
    )


@receiver(view_signals.view_updated)
def view_updated(sender, view, user, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "view_updated",
                "view_id": view.id,
                "view": view_type_registry.get_serializer(
                    view,
                    ViewSerializer,
                    # We do not want to broad cast the filters and sortings every time
                    # the view changes. There are separate views and handlers for them
                    # each will broad cast their own message.
                    filters=False,
                    sortings=False,
                ).data,
            },
            getattr(user, "web_socket_id", None),
            table_id=view.table_id,
        )
    )


@receiver(view_signals.view_deleted)
def view_deleted(sender, view_id, view, user, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: _broadcast_to_users_and_public_views(
            {"type": "view_deleted", "table_id": view.table_id, "view_id": view_id},
            user,
            view,
        )
    )


@receiver(view_signals.views_reordered)
def views_reordered(sender, table, order, user, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {"type": "views_reordered", "table_id": table.id, "order": order},
            getattr(user, "web_socket_id", None),
            table_id=table.id,
        )
    )


def _broadcast_to_users_and_public_views(data, user, view):
    table_page_type = page_registry.get("table")
    table_page_type.broadcast(
        data, getattr(user, "web_socket_id", None), table_id=view.table_id
    )

    broadcast_event_to_view_if_public(view, {"type": "view_changed"})


@receiver(view_signals.view_filter_created)
def view_filter_created(sender, view_filter, user, **kwargs):
    transaction.on_commit(
        lambda: _broadcast_to_users_and_public_views(
            {
                "type": "view_filter_created",
                "view_filter": ViewFilterSerializer(view_filter).data,
            },
            user,
            view_filter.view,
        )
    )


@receiver(view_signals.view_filter_updated)
def view_filter_updated(sender, view_filter, user, **kwargs):
    transaction.on_commit(
        lambda: _broadcast_to_users_and_public_views(
            {
                "type": "view_filter_updated",
                "view_filter_id": view_filter.id,
                "view_filter": ViewFilterSerializer(view_filter).data,
            },
            user,
            view_filter.view,
        )
    )


@receiver(view_signals.view_filter_deleted)
def view_filter_deleted(sender, view_filter_id, view_filter, user, **kwargs):
    transaction.on_commit(
        lambda: _broadcast_to_users_and_public_views(
            {
                "type": "view_filter_deleted",
                "view_id": view_filter.view_id,
                "view_filter_id": view_filter_id,
            },
            user,
            view_filter.view,
        )
    )


@receiver(view_signals.view_sort_created)
def view_sort_created(sender, view_sort, user, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "view_sort_created",
                "view_sort": ViewSortSerializer(view_sort).data,
            },
            getattr(user, "web_socket_id", None),
            table_id=view_sort.view.table_id,
        )
    )


@receiver(view_signals.view_sort_updated)
def view_sort_updated(sender, view_sort, user, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "view_sort_updated",
                "view_sort_id": view_sort.id,
                "view_sort": ViewSortSerializer(view_sort).data,
            },
            getattr(user, "web_socket_id", None),
            table_id=view_sort.view.table_id,
        )
    )


@receiver(view_signals.view_sort_deleted)
def view_sort_deleted(sender, view_sort_id, view_sort, user, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "view_sort_deleted",
                "view_id": view_sort.view_id,
                "view_sort_id": view_sort_id,
            },
            getattr(user, "web_socket_id", None),
            table_id=view_sort.view.table_id,
        )
    )


@receiver(view_signals.before_view_field_options_updated)
def before_view_field_options_updated(sender, view, user, **kwargs):
    view_type = view_type_registry.get_by_model(view.specific_class)
    serializer_class = view_type.get_field_options_serializer_class()
    return serializer_class(view).data["field_options"]


@receiver(view_signals.view_field_options_updated)
def view_field_options_updated(sender, view, user, before_return, **kwargs):
    table_page_type = page_registry.get("table")
    view_type = view_type_registry.get_by_model(view.specific_class)
    serializer_class = view_type.get_field_options_serializer_class()

    def _also_update_public_view():
        serialized_field_options = serializer_class(view).data["field_options"]
        table_page_type.broadcast(
            {
                "type": "view_field_options_updated",
                "view_id": view.id,
                "field_options": serialized_field_options,
            },
            getattr(user, "web_socket_id", None),
            table_id=view.table_id,
        )
        if view.public:
            old_options = dict(before_return)[before_view_field_options_updated]
            old_options_keys = set(old_options.keys())
            new_options_keys = set(serialized_field_options.keys())
            deleted = []
            created = []
            for key in new_options_keys:
                if key in old_options_keys:
                    old_hidden = old_options[key].get("hidden", False)
                    new_hidden = serialized_field_options[key].get("hidden", False)
                    if not old_hidden and new_hidden:
                        deleted.append(key)
                    elif old_hidden and not new_hidden:
                        created.append(key)
                    if new_hidden:
                        serialized_field_options.pop(key)
                # if the key doesn't exist in the old options then is a newly created
                # field options. Here right now we just assume hidden is False by
                # default and send over the options.

            for key in created:
                broadcast_event_to_view_if_public(
                    view,
                    {
                        "type": "field_created",
                        "field": field_type_registry.get_serializer(
                            Field.objects.get(id=key).specific, FieldSerializer
                        ).data,
                        "related_fields": [],
                    },
                )
            for key in deleted:
                field = Field.objects.get(id=key)
                broadcast_event_to_view_if_public(
                    view,
                    {
                        "type": "field_deleted",
                        "table_id": field.table_id,
                        "field_id": field.id,
                    },
                )

            broadcast_event_to_view_if_public(
                view,
                {
                    "type": "view_field_options_updated",
                    "field_options": serialized_field_options,
                    "view_id": view.slug,
                },
            )

    transaction.on_commit(_also_update_public_view)

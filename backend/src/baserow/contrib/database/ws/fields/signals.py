from django.dispatch import receiver
from django.db import transaction

from baserow.contrib.database.ws.public import (
    broadcast_event_to_a_tables_public_views,
    find_public_views_row_is_in,
    find_public_views_field_is_in,
)
from baserow.ws.registries import page_registry

from baserow.contrib.database.fields import signals as field_signals
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.api.fields.serializers import FieldSerializer


def _broadcast_to_table_and_public_views(data, field, user, view_slugs=None):
    table_page_type = page_registry.get("table")
    table_page_type.broadcast(
        data,
        getattr(user, "web_socket_id", None),
        table_id=field.table_id,
    )
    broadcast_event_to_a_tables_public_views(
        field.table, data, field=field, view_slugs=view_slugs
    )


@receiver(field_signals.field_created)
def field_created(sender, field, related_fields, user, **kwargs):
    transaction.on_commit(
        lambda: _broadcast_to_table_and_public_views(
            {
                "type": "field_created",
                "field": field_type_registry.get_serializer(
                    field, FieldSerializer
                ).data,
                "related_fields": [
                    field_type_registry.get_serializer(f, FieldSerializer).data
                    for f in related_fields
                ],
            },
            field,
            user,
        )
    )


@receiver(field_signals.field_restored)
def field_restored(sender, field, related_fields, user, **kwargs):
    transaction.on_commit(
        lambda: _broadcast_to_table_and_public_views(
            {
                "type": "field_restored",
                "field": field_type_registry.get_serializer(
                    field, FieldSerializer
                ).data,
                "related_fields": [
                    field_type_registry.get_serializer(f, FieldSerializer).data
                    for f in related_fields
                ],
            },
            field,
            user,
        )
    )


@receiver(field_signals.field_updated)
def field_updated(sender, field, related_fields, user, **kwargs):
    transaction.on_commit(
        lambda: _broadcast_to_table_and_public_views(
            {
                "type": "field_updated",
                "field_id": field.id,
                "field": field_type_registry.get_serializer(
                    field, FieldSerializer
                ).data,
                "related_fields": [
                    field_type_registry.get_serializer(f, FieldSerializer).data
                    for f in related_fields
                ],
            },
            field,
            user,
        )
    )


@receiver(field_signals.before_field_deleted)
def before_field_deleted(sender, field, user, **kwargs):
    return (find_public_views_field_is_in(field),)


@receiver(field_signals.field_deleted)
def field_deleted(
    sender, field_id, field, related_fields, user, before_return, **kwargs
):
    transaction.on_commit(
        lambda: _broadcast_to_table_and_public_views(
            {
                "type": "field_deleted",
                "table_id": field.table_id,
                "field_id": field_id,
                "related_fields": [
                    field_type_registry.get_serializer(f, FieldSerializer).data
                    for f in related_fields
                ],
            },
            None,
            user,
            dict(before_return)[before_field_deleted],
        )
    )

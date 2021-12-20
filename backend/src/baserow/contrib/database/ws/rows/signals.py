from django.dispatch import receiver
from django.db import transaction

from baserow.contrib.database.rows.registries import row_metadata_registry
from baserow.contrib.database.ws.public import (
    broadcast_event_to_a_tables_public_views,
    find_public_views_row_is_in,
)
from baserow.ws.registries import page_registry

from baserow.contrib.database.rows import signals as row_signals
from baserow.contrib.database.api.rows.serializers import (
    get_row_serializer_class,
    RowSerializer,
)


def _broadcast_to_users_and_public_views(
    data,
    user,
    table,
    model=None,
    row=None,
    view_slugs=None,
    must_send=None,
    must_send_mutator=None,
):
    table_page_type = page_registry.get("table")
    table_page_type.broadcast(
        data, getattr(user, "web_socket_id", None), table_id=table.id
    )

    broadcast_event_to_a_tables_public_views(
        table,
        data,
        model,
        row,
        view_slugs=view_slugs,
        must_send=must_send,
        must_send_mutator=must_send_mutator,
    )


@receiver(row_signals.row_created)
def row_created(sender, row, before, user, table, model, **kwargs):
    transaction.on_commit(
        lambda: _broadcast_to_users_and_public_views(
            {
                "type": "row_created",
                "table_id": table.id,
                "row": get_row_serializer_class(model, RowSerializer, is_response=True)(
                    row
                ).data,
                "metadata": row_metadata_registry.generate_and_merge_metadata_for_row(
                    table, row.id
                ),
                "before_row_id": before.id if before else None,
            },
            user,
            table,
            model,
            row,
        )
    )


@receiver(row_signals.before_row_update)
def before_row_update(sender, row, user, table, model, **kwargs):
    # Generate a serialized version of the row before it is updated. The
    # `row_updated` receiver needs this serialized version because it can't serialize
    # the old row after it has been updated.
    return {
        "old_row": get_row_serializer_class(model, RowSerializer, is_response=True)(
            row
        ).data,
        "public_view_slugs": find_public_views_row_is_in(table, model, row),
    }


@receiver(row_signals.row_updated)
def row_updated(sender, row, user, table, model, before_return, **kwargs):
    def x(d, t):
        d["type"] = f"row_{t}"

    transaction.on_commit(
        lambda: _broadcast_to_users_and_public_views(
            {
                "type": "row_updated",
                "table_id": table.id,
                # The web-frontend expects a serialized version of the row before it
                # was updated in order the estimate what position the row had in the
                # view.
                "row_before_update": dict(before_return)[before_row_update]["old_row"],
                "row": get_row_serializer_class(model, RowSerializer, is_response=True)(
                    row
                ).data,
                "metadata": row_metadata_registry.generate_and_merge_metadata_for_row(
                    table, row.id
                ),
            },
            user,
            table,
            model,
            row,
            must_send=dict(before_return)[before_row_update]["public_view_slugs"],
            must_send_mutator=x,
        )
    )


@receiver(row_signals.before_row_delete)
def before_row_delete(sender, row, user, table, model, **kwargs):
    # Generate a serialized version of the row before it is deleted. The
    # `row_deleted` receiver needs this serialized version because it can't serialize
    # the row after is has been deleted.
    return {
        "old_row": get_row_serializer_class(model, RowSerializer, is_response=True)(
            row
        ).data,
        "public_view_slugs": find_public_views_row_is_in(table, model, row),
    }


@receiver(row_signals.row_deleted)
def row_deleted(sender, row_id, row, user, table, model, before_return, **kwargs):
    transaction.on_commit(
        lambda: _broadcast_to_users_and_public_views(
            {
                "type": "row_deleted",
                "table_id": table.id,
                "row_id": row_id,
                # The web-frontend expects a serialized version of the row that is
                # deleted in order the estimate what position the row had in the view.
                "row": dict(before_return)[before_row_delete]["old_row"],
            },
            user,
            table,
            view_slugs=dict(before_return)[before_row_delete]["public_view_slugs"],
        )
    )

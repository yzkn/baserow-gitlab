import dataclasses
from typing import Any, Dict

from django.contrib.auth.models import AbstractUser

from baserow.core.action.models import Action
from baserow.core.action.registries import ActionType, ActionScopeStr
from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.contrib.database.rows.handler import (
    GeneratedTableModelForUpdate,
    RowHandler,
)
from baserow.contrib.database.table.models import Table
from baserow.core.trash.handler import TrashHandler


class CreateRowActionType(ActionType):
    type = "create_row"

    @dataclasses.dataclass
    class Params:
        table_id: int
        row_id: int

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        table: Table,
        values: Dict[str, Any] = None,
        model: Any = None,
        before: Table = None,
        user_field_names: bool = False,
    ) -> Table:
        """
        Creates a new row for a given table with the provided values if the user
        belongs to the related group. It also calls the row_created signal.
        See the baserow.contrib.database.rows.handler.RowHandler.create_row
        for more information.
        Undoing this action trashes the row and redoing restores it.

        :param user: The user of whose behalf the row is created.
        :param table: The table for which to create a row for.
        :param values: The values that must be set upon creating the row. The keys must
            be the field ids.
        :param model: If a model is already generated it can be provided here to avoid
            having to generate the model again.
        :param before: If provided the new row will be placed right before that row
            instance.
        :param user_field_names: Whether or not the values are keyed by the internal
            Baserow field name (field_1,field_2 etc) or by the user field names.
        :return: The created row instance.
        """

        row = RowHandler().create_row(
            user,
            table,
            values=values,
            model=model,
            before=before,
            user_field_names=user_field_names,
        )
        params = cls.Params(table.id, row.id)
        cls.register_action(user, params, cls.scope(table.id))

        return row

    @classmethod
    def scope(cls, table_id) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        table = Table.objects.get(id=params.table_id)
        RowHandler().delete_row_by_id(user, table, params.row_id)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TrashHandler.restore_item(
            user, "row", params.row_id, parent_trash_item_id=params.table_id
        )


class DeleteRowActionType(ActionType):
    type = "delete_row"

    @dataclasses.dataclass
    class Params:
        table_id: int
        row_id: int

    @classmethod
    def do(cls, user: AbstractUser, table: Table, row_id: int, model: Any = None):
        """
        Deletes an existing row of the given table and with row_id.
        See the baserow.contrib.database.rows.handler.RowHandler.delete_row_by_id
        for more information.
        Undoing this action restores the row and redoing trashes it.

        :param user: The user of whose behalf the change is made.
        :param table: The table for which the row must be deleted.
        :param row_id: The id of the row that must be deleted.
        :param model: If the correct model has already been generated, it can be
            provided so that it does not have to be generated for a second time.
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        """

        RowHandler().delete_row_by_id(user, table, row_id, model=model)
        params = cls.Params(table.id, row_id)
        cls.register_action(user, params, cls.scope(table.id))

    @classmethod
    def scope(cls, table_id) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        TrashHandler.restore_item(
            user, "row", params.row_id, parent_trash_item_id=params.table_id
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        table = Table.objects.get(id=params.table_id)
        RowHandler().delete_row_by_id(user, table, params.row_id)


class MoveRowActionType(ActionType):
    type = "move_row"

    @dataclasses.dataclass
    class Params:
        table_id: int
        row_id: int
        original_before_row_id: int
        new_before_row_id: int

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        table: Table,
        row: GeneratedTableModelForUpdate,
        before: Table = None,
        model: Any = None,
    ) -> GeneratedTableModelForUpdate:
        """
        Moves the row before another row or to the end if no before row is provided.
        This moving is done by updating the `order` value of the order.
        See the baserow.contrib.database.rows.handler.RowHandler.move_row
        for more information.
        Undoing this action restores the original row position and redoing move it
        at the new position again.

        :param user: The user of whose behalf the row is moved
        :param table: The table that contains the row that needs to be moved.
        :param row: The row that needs to be moved.
        :param before: If provided the new row will be placed right before that row
            instance. Otherwise the row will be moved to the end.
        :param model: If the correct model has already been generated, it can be
            provided so that it does not have to be generated for a second time.
        """

        row_handler = RowHandler()
        original_row_before = (
            model.objects.order_by("order").filter(order__gt=row.order).first()
        )
        original_row_before_id = original_row_before.id if original_row_before else None
        updated_row = row_handler.move_row(user, table, row, before=before, model=model)

        params = cls.Params(
            table.id, row.id, original_row_before_id, before.id if before else None
        )
        cls.register_action(user, params, cls.scope(table.id))

        return updated_row

    @classmethod
    def scope(cls, table_id) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        table = Table.objects.get(id=params.table_id)
        row_handler = RowHandler()

        model = table.get_model()

        before_id = params.original_before_row_id
        before = (
            row_handler.get_row(user, table, before_id, model) if before_id else None
        )

        row = row_handler.get_row_for_update(user, table, params.row_id, model)
        row_handler.move_row(user, table, row, before=before)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        table = Table.objects.get(id=params.table_id)
        row_handler = RowHandler()

        model = table.get_model()

        before_id = params.new_before_row_id
        before = (
            row_handler.get_row(user, table, before_id, model) if before_id else None
        )

        row = row_handler.get_row_for_update(user, table, params.row_id, model)
        row_handler.move_row(user, table, row, before=before)

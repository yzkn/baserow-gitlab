import dataclasses
from typing import Any, List

from django.contrib.auth.models import AbstractUser

from baserow.core.action.models import Action
from baserow.core.action.registries import ActionType, ActionScopeStr
from baserow.core.action.scopes import ApplicationActionScopeType
from baserow.core.trash.handler import TrashHandler
from baserow.contrib.database.models import Database
from baserow.contrib.database.table.handler import TableForUpdate, TableHandler
from baserow.contrib.database.table.models import Table


class CreateTableActionType(ActionType):
    type = "create_table"

    @dataclasses.dataclass
    class Params:
        table_id: int

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        database: Database,
        name: str,
        fill_example: bool = False,
        data: List[List[str]] = None,
        first_row_header: bool = True,
    ) -> Table:
        """
        Creates a new table in the databse.
        See baserow.contrib.database.table.handler.TableHandler.create_table
        for further details.
        Undoing this action trashes the table and redoing restores it.

        :param user: The user on whose behalf the table is created.
        :param database: The database that the table instance belongs to.
        :param name: The name of the table is created.
        :param fill_example: Indicates whether an initial view, some fields and
            some rows should be added. Works only if no data is provided.
        :param data: A list containing all the rows that need to be inserted is
            expected. All the values of the row are going to be converted to a string
            and will be inserted in the database.
        :param first_row_header: Indicates if the first row are the fields. The names
            of these rows are going to be used as fields.
        :raises MaxFieldLimitExceeded: When the data contains more columns
            than the field limit.
        :return: The created table instance.
        """

        table = TableHandler().create_table(
            user,
            database,
            name,
            fill_example=fill_example,
            data=data,
            first_row_header=first_row_header,
        )

        params = cls.Params(table.id)
        cls.register_action(user, params, cls.scope(database.id))

        return table

    @classmethod
    def scope(cls, database_id) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        table = Table.objects.get(id=params.table_id)
        TableHandler().delete_table(user, table)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TrashHandler.restore_item(
            user, "table", params.table_id, parent_trash_item_id=None
        )


class DeleteTableActionType(ActionType):
    type = "delete_table"

    @dataclasses.dataclass
    class Params:
        table_id: int

    @classmethod
    def do(cls, user: AbstractUser, table: Table) -> Any:
        """
        Deletes a table in the databse.
        See baserow.contrib.database.table.handler.TableHandler.delete_table
        for further details.
        Undoing this action restore the original table from trash and redoing trash it.

        :param user: The user on whose behalf the table is deleted.
        :param table: The table instance that needs to be deleted.
        :raises ValueError: When the provided table is not an instance of Table.
        """

        params = cls.Params(table.id)

        TableHandler().delete_table(user, table)

        cls.register_action(user, params, cls.scope(table.database.id))

    @classmethod
    def scope(cls, database_id) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        TrashHandler.restore_item(
            user, "table", params.table_id, parent_trash_item_id=None
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        table = Table.objects.get(id=params.table_id)
        TableHandler().delete_table(user, table)


class OrderTableActionType(ActionType):
    type = "order_table"

    @dataclasses.dataclass
    class Params:
        database_id: int
        original_tables_order: List[int]
        new_tables_order: List[int]

    @classmethod
    def do(cls, user: AbstractUser, database: Database, order: List[int]) -> Table:
        """
        Updates the order of the tables in the given database.
        See baserow.contrib.database.table.handler.TableHandler.order_table
        for further details.
        Undoing this action restore the previous order and redoing set the new order.

        :param user: The user on whose behalf the tables are ordered.
        :param database: The database of which the views must be updated.
        :param order: A list containing the table ids in the desired order.
        :raises TableNotInDatabase: If one of the table ids in the order does not belong
            to the database.
        """

        original_table_order = [t.id for t in database.table_set.order_by("order")]
        params = cls.Params(database.id, original_table_order, new_tables_order=order)

        TableHandler().order_tables(user, database, order=order)

        cls.register_action(user, params, cls.scope(database.database.id))

    @classmethod
    def scope(cls, database_id) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        database = Database.objects.get(id=params.database_id)
        TableHandler().order_tables(user, database, order=params.original_tables_order)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        database = Database.objects.get(id=params.database_id)
        TableHandler().order_tables(user, database, order=params.new_tables_order)


class UpdateTableActionType(ActionType):
    type = "update_table"

    @dataclasses.dataclass
    class Params:
        table_id: int
        original_table_name: str
        new_table_name: str

    @classmethod
    def do(cls, user: AbstractUser, table: TableForUpdate, name: str) -> TableForUpdate:
        """
        Updates the table.
        See baserow.contrib.database.table.handler.TableHandler.update_table
        for further details.
        Undoing this action restore the original table name and redoing
        set the new name again.

        :param user: The user on whose behalf the table is updated.
        :param table: The table instance that needs to be updated.
        :param kwargs: The fields that need to be updated.
        :raises ValueError: When the provided table is not an instance of Table.
        :return: The updated table instance.
        """

        params = cls.Params(
            table.id,
            original_table_name=table.name,
            new_table_name=name,
        )

        table = TableHandler().update_table(user, table, name=name)

        cls.register_action(user, params, cls.scope(table.database.id))
        return table

    @classmethod
    def scope(cls, database_id) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        table = Table.objects.get(id=params.table_id)
        TableHandler().update_table(user, table, name=params.original_table_name)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        table = Table.objects.get(id=params.table_id)
        TableHandler().update_table(user, table, name=params.new_table_name)

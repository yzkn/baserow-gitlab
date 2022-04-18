import dataclasses
import typing
from copy import deepcopy

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View, ViewFilter, ViewSort
from baserow.core.action.models import Action
from baserow.core.action.registries import ActionScopeStr, ActionType
from baserow.core.action.scopes import ApplicationActionScopeType
from django.contrib.auth import get_user_model

UserType = get_user_model()


class CreateViewFilterActionType(ActionType):
    type = "create_view_filter"

    @dataclasses.dataclass
    class Params:
        view_id: int
        field_id: int
        filter_type: str
        filter_value: str

    @classmethod
    def do(
        cls,
        user: UserType,
        view_id: int,
        field_id: int,
        filter_type: str,
        filter_value: str,
    ) -> ViewFilter:
        """
        Creates a new filter for the provided view.

        :param user: The user creating the filter.
        :param view_id: The id of the view to create the filter for.
        :param field_id: The id of the field to filter by.
        :param filter_type: Indicates how the field's value
        must be compared to the filter's value.
        :param filter_value: The filter value that must be
        compared to the field's value.
        """

        view_handler = ViewHandler()
        view = view_handler.get_view(view_id)
        field = Field.objects.get(pk=field_id)
        view_filter = view_handler.create_filter(
            user, view, field, filter_type, filter_value
        )
        cls.register_action(
            user=user,
            params=cls.Params(view_id, field_id, filter_type, filter_value),
            scope=cls.scope(view.table.database.id),
        )
        return view_filter

    @classmethod
    def scope(cls, database_id: int) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: UserType, params: Params, action_to_undo: Action):
        field = Field.objects.get(pk=params.field_id)
        view = View.objects.get(pk=params.view_id)

        view_filter = ViewFilter.objects.filter(
            view=view, field=field, type=params.filter_type, value=params.filter_value
        ).first()

        ViewHandler().delete_filter(user, view_filter)

    @classmethod
    def redo(cls, user: UserType, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view(params.view_id)
        field = Field.objects.get(pk=params.field_id)
        view_handler.create_filter(
            user, view, field, params.filter_type, params.filter_value
        )


class UpdateViewFilterActionType(ActionType):
    type = "update_view_filter"

    @dataclasses.dataclass
    class Params:
        view_filter_id: int
        old_field_id: int
        old_filter_type: str
        old_filter_value: str
        new_field_id: int
        new_filter_type: str
        new_filter_value: str

    @classmethod
    def do(
        cls,
        user: UserType,
        view_filter: ViewFilter,
        field: typing.Optional[Field] = None,
        filter_type: typing.Optional[str] = None,
        filter_value: typing.Optional[str] = None,
    ) -> ViewFilter:
        """
        Updates the values of an existing view filter.

        :param user: The user on whose behalf the view filter is updated.
        :param view_filter: The view filter that needs to be updated.
        :param field: The model of the field to filter by.
        :param filter_type: Indicates how the field's value
        must be compared to the filter's value.
        :param filter_value: The filter value that must be
        compared to the field's value.
        """

        data = {}
        if field is not None:
            data["field"] = field
        if filter_type is not None:
            data["type_name"] = filter_type
        if filter_value is not None:
            data["value"] = filter_value

        old_view_filter = deepcopy(view_filter)
        view_handler = ViewHandler()
        updated_view_filter = view_handler.update_filter(user, view_filter, **data)
        cls.register_action(
            user=user,
            params=cls.Params(
                view_filter.id,
                old_view_filter.field.id,
                old_view_filter.type,
                old_view_filter.value,
                updated_view_filter.field.id,
                updated_view_filter.type,
                updated_view_filter.value,
            ),
            scope=cls.scope(view_filter.view.table.database.id),
        )

        return updated_view_filter

    @classmethod
    def scope(cls, database_id: int) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: UserType, params: Params, action_to_undo: Action):
        field = Field.objects.get(pk=params.old_field_id)

        view_handler = ViewHandler()
        view_filter = view_handler.get_filter(user, params.view_filter_id)

        data = {"field": field}
        if params.old_filter_type is not None:
            data["type_name"] = params.old_filter_type
        if params.old_filter_value is not None:
            data["value"] = params.old_filter_value

        view_handler.update_filter(user, view_filter, **data)

    @classmethod
    def redo(cls, user: UserType, params: Params, action_to_redo: Action):
        field = Field.objects.get(pk=params.new_field_id)

        view_handler = ViewHandler()
        view_filter = view_handler.get_filter(user, params.view_filter_id)

        data = {"field": field}
        if params.new_filter_type is not None:
            data["type_name"] = params.new_filter_type
        if params.new_filter_value is not None:
            data["value"] = params.new_filter_value

        view_handler.update_filter(user, view_filter, **data)


class DeleteViewFilterActionType(ActionType):
    type = "delete_view_filter"

    @dataclasses.dataclass
    class Params:
        view_id: int
        field_id: int
        filter_type: str
        filter_value: str

    @classmethod
    def do(
        cls,
        user: UserType,
        view_filter_id: int,
    ):
        """
        Deletes an existing view filter.

        :param user: The user on whose behalf the view filter is deleted.
        :param view_filter_id: The id of the view filter that needs to be deleted.
        """

        view_handler = ViewHandler()
        view_filter = view_handler.get_filter(user, view_filter_id)
        view_handler.delete_filter(user, view_filter)

        cls.register_action(
            user=user,
            params=cls.Params(
                view_filter.view.id,
                view_filter.field.id,
                view_filter.type,
                view_filter.value,
            ),
            scope=cls.scope(view_filter.view.table.database.id),
        )

    @classmethod
    def scope(cls, database_id: int) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: UserType, params: Params, action_to_undo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view(params.view_id)
        field = Field.objects.get(pk=params.field_id)

        view_handler.create_filter(
            user, view, field, params.filter_type, params.filter_value
        )

    @classmethod
    def redo(cls, user: UserType, params: Params, action_to_redo: Action):
        field = Field.objects.get(pk=params.field_id)
        view = View.objects.get(pk=params.view_id)

        view_filter = ViewFilter.objects.filter(
            view=view, field=field, type=params.filter_type, value=params.filter_value
        ).first()

        ViewHandler().delete_filter(user, view_filter)


class CreateViewSortActionType(ActionType):
    type = "create_view_sort"

    @dataclasses.dataclass
    class Params:
        view_id: int
        field_id: int
        sort_order: str

    @classmethod
    def do(
        cls, user: UserType, view_id: int, field_id: int, sort_order: str
    ) -> ViewSort:
        """
        Creates a new view sort.

        :param user: The user on whose behalf the view sort is created.
        :param view_id: The id of the view for which the sort needs to be created.
        :param field_id: The id of the field that needs to be sorted.
        :param sort_order: The desired order, can either be ascending (A to Z) or
            descending (Z to A).
        """

        view_handler = ViewHandler()
        view = view_handler.get_view(view_id)
        field = Field.objects.get(pk=field_id)
        view_sort = view_handler.create_sort(user, view, field, sort_order)

        cls.register_action(
            user=user,
            params=cls.Params(view_id, field_id, sort_order),
            scope=cls.scope(view.table.database.id),
        )
        return view_sort

    @classmethod
    def scope(cls, database_id: int) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: UserType, params: Params, action_to_undo: Action):
        field = Field.objects.get(pk=params.field_id)
        view = View.objects.get(pk=params.view_id)

        view_sort = ViewSort.objects.filter(
            view=view, field=field, order=params.sort_order
        ).first()

        ViewHandler().delete_sort(user, view_sort)

    @classmethod
    def redo(cls, user: UserType, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view(params.view_id)
        field = Field.objects.get(pk=params.field_id)

        view_handler.create_sort(user, view, field, params.sort_order)

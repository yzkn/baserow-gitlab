import dataclasses

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import ViewFilter
from baserow.core.action.models import Action
from baserow.core.action.registries import ActionScopeStr, ActionType
from baserow.core.action.scopes import ApplicationActionScopeType
from django.contrib.auth import get_user_model

UserType = get_user_model()


class CreateViewFilterActionType(ActionType):
    type = "create_view_filter"

    @dataclasses.dataclass
    class Params:
        view_filter_id: int
        view_id: int
        field_id: int
        field_type: str
        filter_value: str

    @classmethod
    def do(
        cls,
        view_id: int,
        user: UserType,
        field_id: int,
        field_type: str,
        filter_value: str,
    ) -> ViewFilter:
        """
        Creates a new filter for the provided view.

        :param view_id: The id of the view to create the filter for.
        :param user: The user creating the filter.
        :param field_id: The id of the field to filter by.
        :param field_type: Indicates how the field's value
        must be compared to the filter's value.
        :param filter_value: The filter value that must be
        compared to the field's value.
        """

        view_handler = ViewHandler()
        view = view_handler.get_view(view_id)
        field = Field.objects.get(pk=field_id)
        view_filter = view_handler.create_filter(
            user, view, field, field_type, filter_value
        )
        cls.register_action(
            user=user,
            params=cls.Params(
                view_filter.id, view_id, field_id, field_type, filter_value
            ),
            scope=cls.scope(view.table.database.id),
        )
        return view_filter

    @classmethod
    def scope(cls, database_id: int) -> ActionScopeStr:
        return ApplicationActionScopeType.value(database_id)

    @classmethod
    def undo(cls, user: UserType, params: Params, action_to_undo: Action):
        view_handler = ViewHandler()
        view_filter = view_handler.get_filter(user, params.view_filter_id)
        view_handler.delete_filter(user, view_filter)

    @classmethod
    def redo(cls, user: UserType, params: Params, action_to_redo: Action):
        view_handler = ViewHandler()
        view = view_handler.get_view(params.view_id)
        field = Field.objects.get(pk=params.field_id)
        view_handler.create_filter(
            user, view, field, params.field_type, params.filter_value
        )

import dataclasses
from typing import Any

from baserow.core.actions.scopes import GroupActionScopeType
from baserow.core.actions.models import Action
from baserow.core.actions.registries import ActionType, ActionScopeStr
from baserow.core.handler import CoreHandler
from baserow.core.models import Group, Application
from baserow.core.trash.handler import TrashHandler
from baserow.core.user.utils import UserType


class CreateApplicationActionType(ActionType['CreateApplicationActionType.Params']):
    type = 'create_application'

    @dataclasses.dataclass
    class Params:
        application_id: int

    @classmethod
    def do(cls, user: UserType, group: Group, application_type: str, name: str) -> Any:
        application = CoreHandler().create_application(user, group, application_type, name=name)

        params = cls.Params(application.id)
        cls.register_action(user, params, cls.scope(group.id))

        return application

    @classmethod
    def scope(cls, group_id) -> ActionScopeStr:
        return GroupActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: UserType, params: Params, action_being_undone: Action):
        application = Application.objects.get(id=params.application_id)
        CoreHandler().delete_application(user, application)

    @classmethod
    def redo(cls, user: UserType, params: Params, action_being_redone: Action):
        TrashHandler.restore_item(
            user, "application", params.application_id, parent_trash_item_id=None
        )

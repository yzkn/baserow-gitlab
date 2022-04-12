import dataclasses
from typing import Any

from baserow.core.actions.categories import GroupActionCategoryType
from baserow.core.actions.models import Action
from baserow.core.actions.registries import ActionType, T, ActionCategoryStr
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
        cls.register_action(user, params, cls.default_category(group.id))

        return application

    @classmethod
    def default_category(cls, group_id) -> ActionCategoryStr:
        return GroupActionCategoryType.value(group_id)

    @classmethod
    def undo(cls, user: UserType, params: Params, action_being_undone: Action):
        application = Application.objects.get(id=params.application_id)
        CoreHandler().delete_application(user, application)

    @classmethod
    def redo(cls, user: UserType, params: Params, action_being_redone: Action):
        TrashHandler.restore_item(
            user, "application", params.application_id, parent_trash_item_id=None
        )

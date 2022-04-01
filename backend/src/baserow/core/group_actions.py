import dataclasses

from django.contrib.auth import get_user_model

from baserow.core.actions.models import Action
from baserow.core.actions.registries import ActionType
from baserow.core.actions.categories import RootActionCategoryType
from baserow.core.handler import CoreHandler, LockedGroup
from baserow.core.models import Group, GroupUser
from baserow.core.trash.handler import TrashHandler
from baserow.core.user.utils import UserType

User = get_user_model()


class DeleteGroupActionType(ActionType["DeleteGroupAction.Params"]):
    type = "delete_group"

    @dataclasses.dataclass
    class Params:
        group_id: int

    def do(self, user: UserType, group: LockedGroup):
        CoreHandler().delete_group(user, group)

        self.register_action(
            user,
            self.Params(group.id),
            category=RootActionCategoryType.value(),
        )

    @classmethod
    def undo(
        cls,
        user: UserType,
        params: "DeleteGroupActionType.Params",
        action_to_undo: Action,
    ):
        TrashHandler.restore_item(
            user,
            "group",
            params.group_id,
        )

    @classmethod
    def redo(
        cls,
        user: UserType,
        params: "DeleteGroupActionType.Params",
        action_to_redo: Action,
    ):
        CoreHandler().delete_group_by_id(user, params.group_id)


class CreateGroupActionType(ActionType["CreateGroupParameters"]):
    type = "create_group"

    @dataclasses.dataclass
    class Params:
        created_group_id: int
        group_name: str

    @classmethod
    def do(cls, user: UserType, group_name: str) -> GroupUser:
        group_user = CoreHandler().create_group(user, name=group_name)

        # noinspection PyTypeChecker
        group_id: int = group_user.group_id

        cls.register_action(
            user=user,
            params=cls.Params(group_id, group_name),
            category=RootActionCategoryType.value(),
        )
        return group_user

    @classmethod
    def undo(
        cls,
        user: UserType,
        params: "CreateGroupActionType.Params",
        action_to_undo: Action,
    ):
        CoreHandler().delete_group_by_id(user, params.created_group_id)

    @classmethod
    def redo(
        cls,
        user: UserType,
        params: "CreateGroupActionType.Params",
        action_to_redo: Action,
    ):
        TrashHandler.restore_item(
            user, "group", params.created_group_id, parent_trash_item_id=None
        )


class UpdateGroupActionType(ActionType["Params"]):
    type = "update_group"

    @dataclasses.dataclass
    class Params:
        updated_group_id: int
        old_group_name: str
        new_group_name: str

    @classmethod
    def do(cls, user: UserType, group: LockedGroup, new_group_name: str) -> Group:
        old_group_name = group.name
        CoreHandler().update_group(user, group, name=new_group_name)

        cls.register_action(
            user=user,
            params=cls.Params(
                group.id,
                old_group_name=old_group_name,
                new_group_name=new_group_name,
            ),
            category=RootActionCategoryType.value(),
        )
        return group

    @classmethod
    def undo(
        cls,
        user: UserType,
        params: "UpdateGroupActionType.Params",
        action_to_undo: Action,
    ):
        group = CoreHandler().get_group_for_update(params.updated_group_id)
        CoreHandler().update_group(
            user,
            group,
            name=params.old_group_name,
        )

    @classmethod
    def redo(
        cls,
        user: UserType,
        params: "UpdateGroupActionType.Params",
        action_to_redo: Action,
    ):
        group = CoreHandler().get_group_for_update(params.updated_group_id)
        CoreHandler().update_group(
            user,
            group,
            name=params.new_group_name,
        )

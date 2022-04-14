import dataclasses

from django.contrib.auth import get_user_model

from baserow.core.actions.scopes import RootActionScopeType
from baserow.core.actions.models import Action
from baserow.core.actions.registries import (
    ActionType,
    ActionScopeStr,
)
from baserow.core.handler import CoreHandler, LockedGroup
from baserow.core.models import Group, GroupUser
from baserow.core.trash.handler import TrashHandler
from baserow.core.user.utils import UserType

User = get_user_model()


class DeleteGroupActionType(ActionType["DeleteGroupAction.Params"]):
    type = "delete_group"

    @dataclasses.dataclass
    class Params:
        deleted_group_id: int

    def do(self, user: UserType, group: LockedGroup):
        """
        Deletes an existing group and related applications if the user has admin
        permissions for the group. See baserow.core.handler.CoreHandler.delete_group
        for more details. Undoing this action restores the group, redoing it deletes it
        again.

        :param user: The user performing the delete.
        :param group: A LockedGroup obtained from CoreHandler.get_group_for_update which
            will be deleted.
        """

        CoreHandler().delete_group(user, group)

        self.register_action(user, self.Params(group.id), scope=self.scope())

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()

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
            params.deleted_group_id,
        )

    @classmethod
    def redo(
        cls,
        user: UserType,
        params: "DeleteGroupActionType.Params",
        action_to_redo: Action,
    ):
        CoreHandler().delete_group_by_id(user, params.deleted_group_id)


class CreateGroupActionType(ActionType["CreateGroupParameters"]):
    type = "create_group"

    @dataclasses.dataclass
    class Params:
        created_group_id: int
        group_name: str

    @classmethod
    def do(cls, user: UserType, group_name: str) -> GroupUser:
        """
        Creates a new group for an existing user. See
        baserow.core.handler.CoreHandler.create_group for more details. Undoing this
        action deletes the created group, redoing it restores it from the trash.

        :param user: The user creating the group.
        :param group_name: The name to give the group.
        """

        group_user = CoreHandler().create_group(user, name=group_name)

        # noinspection PyTypeChecker
        group_id: int = group_user.group_id

        cls.register_action(
            user=user,
            params=cls.Params(group_id, group_name),
            scope=cls.scope(),
        )
        return group_user

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()

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
        """
        Updates the values of a group if the user has admin permissions to the group.
        See baserow.core.handler.CoreHandler.upgrade_group for more details. Undoing
        this action restores the name of the group prior to this action being performed,
        redoing this restores the new name set initially.

        :param user: The user creating the group.
        :param group: A LockedGroup obtained from CoreHandler.get_group_for_update on
            which the update will be run.
        :param new_group_name: The new name to give the group.
        """

        old_group_name = group.name
        CoreHandler().update_group(user, group, name=new_group_name)

        cls.register_action(
            user=user,
            params=cls.Params(
                group.id,
                old_group_name=old_group_name,
                new_group_name=new_group_name,
            ),
            scope=cls.scope(),
        )
        return group

    @classmethod
    def scope(cls) -> ActionScopeStr:
        return RootActionScopeType.value()

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

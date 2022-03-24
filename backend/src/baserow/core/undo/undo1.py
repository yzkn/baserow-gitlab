import abc
import dataclasses
from typing import TypeVar, Generic, Type, Optional

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import utc

from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GroupUser, GROUP_USER_PERMISSION_ADMIN
from baserow.core.registry import Registry, Instance
from baserow.core.signals import group_created, group_updated
from baserow.core.trash.handler import TrashHandler
from baserow.core.undo.models import Action

User = get_user_model()


class BaserowActionRegistry(Registry):
    name = "action"


action_registry = BaserowActionRegistry()


def setup_registry():
    action_registry.register(CreateGroupAction())
    action_registry.register(DeleteGroupAction())
    action_registry.register(RestoreAction())
    action_registry.register(UpdateGroupAction())


T = TypeVar("T")


class RootScope:
    scope_list = ["root"]

    @property
    def scope(self):
        return ".".join(self.scope_list)

    @property
    def scope_q(self):
        q = Q()
        for scope in self.scope_list:
            q |= Q(scope=scope)
        return q


class BaserowAction(Instance, abc.ABC, Generic[T]):
    @property
    @abc.abstractmethod
    def type(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def params_class(self) -> Type[T]:
        pass

    @classmethod
    @abc.abstractmethod
    def redo(cls, user: User, params: T):
        pass

    @classmethod
    @abc.abstractmethod
    def undo(cls, user: User, params: T):
        pass

    @classmethod
    def register_action(
        cls,
        user: User,
        params: T,
        scope: RootScope,
    ):
        Action.objects.create(
            user=user, type=cls.type, params=params, scope=scope.scope
        )


class GroupActionScope(RootScope):
    def __init__(self, group_pk: int):
        self.scope_list = super().scope_list + [f"group{group_pk}"]


@dataclasses.dataclass
class RestoreParameters:
    trash_item_type: str
    trash_item_id: int
    parent_trash_item_id: Optional[int]
    delete_action_type: str


@dataclasses.dataclass
class DeleteParameters:
    id: int
    parent_id: Optional[int] = None


class RestoreAction(BaserowAction[RestoreParameters]):
    type = "restore"
    params_class = RestoreParameters

    @classmethod
    def restore(
        cls,
        user: User,
        trash_item_type: str,
        trash_item_id: int,
        delete_action_type: str,
        register_action: bool,
        parent_trash_item_id: Optional[int] = None,
    ):
        TrashHandler.restore_item(
            user,
            trash_item_type,
            trash_item_id,
            parent_trash_item_id,
        )
        if register_action:
            cls.register_action(
                user=user,
                params=RestoreParameters(
                    trash_item_type,
                    trash_item_id,
                    parent_trash_item_id,
                    delete_action_type,
                ),
                scope=RootScope(),
            )

    @classmethod
    def redo(
        cls,
        user: User,
        params: RestoreParameters,
        undoes: Optional[Action] = None,
    ):
        cls.restore(
            user,
            params.trash_item_type,
            params.trash_item_id,
            params.delete_action_type,
            register_action=True,
            parent_trash_item_id=params.parent_trash_item_id,
        )

    @classmethod
    def undo(cls, user: User, params: RestoreParameters):
        delete_action_type = action_registry.get(params.delete_action_type)
        delete_action_type.do(
            user,
            DeleteParameters(
                id=params.trash_item_id, parent_id=params.parent_trash_item_id
            ),
        )


class DeleteGroupAction(BaserowAction[DeleteParameters]):
    type = "delete_group"
    params_class = DeleteParameters

    @classmethod
    def delete_group(cls, user: User, group_id: int, register_action: bool):
        group = CoreHandler().get_group(
            group_id, base_queryset=Group.objects.select_for_update()
        )
        CoreHandler().delete_group(user, group)
        if register_action:
            cls.register_action(
                user,
                DeleteParameters(id=group.id),
                scope=GroupActionScope(group.id),
            )

    @classmethod
    def redo(cls, user: User, params: DeleteParameters):
        cls.delete_group(user, params.id, register_action=False)

    @classmethod
    def undo(cls, user: User, params: DeleteParameters):
        RestoreAction.restore(user, "group", params.id, cls.type, register_action=False)


@dataclasses.dataclass
class CreateGroupParameters:
    created_group_id: int
    group_name: str


class CreateGroupAction(BaserowAction[CreateGroupParameters]):
    type = "create_group"
    params_class = CreateGroupParameters

    @classmethod
    def create_group(
        cls, user: User, group_name: str, register_action: bool
    ) -> GroupUser:
        group = Group.objects.create(name=group_name)
        last_order = GroupUser.get_last_order(user)
        group_user = GroupUser.objects.create(
            group=group,
            user=user,
            order=last_order,
            permissions=GROUP_USER_PERMISSION_ADMIN,
        )
        group_created.send(cls, group=group, user=user)

        if register_action:
            cls.register_action(
                user=user,
                params=CreateGroupParameters(group.id, group_name),
                scope=RootScope(),
            )
        return group_user

    @classmethod
    def redo(cls, user: User, params: CreateGroupParameters):
        DeleteGroupAction.undo(user, DeleteParameters(params.created_group_id))

    @classmethod
    def undo(cls, user: User, params: CreateGroupParameters):
        DeleteGroupAction.delete_group(
            user, params.created_group_id, register_action=False
        )


@dataclasses.dataclass
class UpdateGroupParameters:
    updated_group_id: int
    old_group_name: str
    new_group_name: str


class UpdateGroupAction(BaserowAction[UpdateGroupParameters]):
    type = "update_group"
    params_class = UpdateGroupParameters

    @classmethod
    def update_group(
        cls, user: User, group: Group, new_group_name: str, register_action: bool
    ) -> Group:
        if not isinstance(group, Group):
            raise ValueError("The group is not an instance of Group.")

        group.has_user(user, "ADMIN", raise_error=True)
        old_group_name = group.name
        group.name = new_group_name
        group.save()

        group_updated.send(cls, group=group, user=user)

        group_created.send(cls, group=group, user=user)
        if register_action:
            cls.register_action(
                user=user,
                params=UpdateGroupParameters(
                    group.id,
                    old_group_name=old_group_name,
                    new_group_name=new_group_name,
                ),
                scope=GroupActionScope(group.id),
            )
        return group

    @classmethod
    def redo(cls, user: User, params: UpdateGroupParameters):
        cls.update_group(
            user,
            Group.objects.get(id=params.updated_group_id),
            new_group_name=params.new_group_name,
            register_action=False,
        )

    @classmethod
    def undo(cls, user: User, params: UpdateGroupParameters):
        cls.update_group(
            user,
            Group.objects.get(id=params.updated_group_id),
            new_group_name=params.old_group_name,
            register_action=False,
        )


class ActionHandler:
    @classmethod
    def undo(cls, user: User, scope: RootScope):
        latest_not_undone_action_in_scope = (
            Action.objects.filter(user=user, undone_at__isnull=True)
            .filter(scope.scope_q)
            .select_for_update()
            .first()
        )
        if latest_not_undone_action_in_scope is None:
            return False
        action_type = action_registry.get(latest_not_undone_action_in_scope.type)
        latest_params = action_type.params_class(
            **latest_not_undone_action_in_scope.params
        )
        try:
            action_type.undo(user, latest_params)
        finally:
            latest_not_undone_action_in_scope.undone_at = timezone.now()
            latest_not_undone_action_in_scope.save()

        return True

    @classmethod
    def redo(cls, user: User, scope: RootScope):
        latest_undone_action_in_scope = (
            Action.objects.filter(user=user, undone_at__isnull=False)
            .filter(scope.scope_q)
            .order_by("-undone_at")
            .select_for_update()
            .first()
        )

        # There have been no undoes
        if latest_undone_action_in_scope is None:
            return False

        normal_action_happened_since_undo = (
            Action.objects.filter(
                user=user,
                created_on__gt=latest_undone_action_in_scope.undone_at,
                undone_at__isnull=True,
            )
            .filter(scope.scope_q)
            .exists()
        )
        if normal_action_happened_since_undo:
            return False

        action_type = action_registry.get(latest_undone_action_in_scope.type)
        latest_params = action_type.params_class(**latest_undone_action_in_scope.params)
        action_type.redo(user, latest_params)
        latest_undone_action_in_scope.undone_at = None
        latest_undone_action_in_scope.save()
        return True

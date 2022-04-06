import dataclasses
from typing import Optional

from django.contrib.auth import get_user_model

from baserow.core.actions.models import Action
from baserow.core.actions.registries import (
    ActionType,
    ActionCategoryStr,
    action_type_registry,
)
from baserow.core.actions.categories import RootActionCategoryType
from baserow.core.trash.handler import TrashHandler

User = get_user_model()


@dataclasses.dataclass
class DeleteParams:
    trash_item_id: int
    parent_trash_item_id: Optional[int] = None


class RestoreActionType(ActionType["Params"]):
    type = "restore"

    @dataclasses.dataclass
    class Params:
        delete_action_type: str
        trash_item_type: str
        trash_item_id: int
        parent_trash_item_id: Optional[int]

    @classmethod
    def do(
        cls,
        user: User,
        delete_action_type: str,
        trash_item_type: str,
        trash_item_id: int,
        parent_trash_item_id: Optional[int] = None,
    ):
        TrashHandler.restore_item(
            user,
            trash_item_type,
            trash_item_id,
            parent_trash_item_id,
        )
        cls.register_action(
            user=user,
            params=cls.Params(
                delete_action_type,
                trash_item_type,
                trash_item_id,
                parent_trash_item_id,
            ),
            category=cls.default_category(),
        )

    @classmethod
    def default_category(cls) -> ActionCategoryStr:
        return RootActionCategoryType.value()

    @classmethod
    def undo(
        cls, user: User, params: "RestoreActionType.Params", action_being_undone: Action
    ):
        action_type_registry.get(params.delete_action_type).redo(
            user,
            DeleteParams(
                params.trash_item_type,
                params.trash_item_id,
                params.parent_trash_item_id,
            ),
            action_being_undone,
        )
        return action_being_undone

    @classmethod
    def redo(
        cls, user: User, params: "RestoreActionType.Params", action_being_redone: Action
    ):
        TrashHandler.restore_item(
            user,
            params.trash_item_type,
            params.trash_item_id,
            parent_trash_item_id=params.parent_trash_item_id,
        )

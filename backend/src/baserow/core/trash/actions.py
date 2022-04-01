import dataclasses
from typing import Optional

from django.contrib.auth import get_user_model

from baserow.core.actions.models import Action
from baserow.core.actions.registries import ActionType
from baserow.core.actions.categories import RootActionCategoryType
from baserow.core.trash.handler import TrashHandler

User = get_user_model()


class RestoreActionType(ActionType["Params"]):
    type = "restore"

    @dataclasses.dataclass
    class Params:
        trash_item_type: str
        trash_item_id: int
        parent_trash_item_id: Optional[int]

    @classmethod
    def do(
        cls,
        user: User,
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
                trash_item_type,
                trash_item_id,
                parent_trash_item_id,
            ),
            category=RootActionCategoryType.value(),
        )

    @classmethod
    def undo(
        cls, user: User, params: "RestoreActionType.Params", action_being_undone: Action
    ):
        # todo this is painful without a trash system which lets us delete just using
        # an id and a trash_item_type. TrashHandler.restore_item works this way already.
        # We could instead store in RestoreAction.Params.delete_action_type the correct
        # action to delete the trashable item type. Then when we undo we call
        # action_registry.get(params.delete_action_type).redo which will do the delete
        # correctly.
        pass

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

import dataclasses
from typing import Optional

from django.contrib.auth import get_user_model

from baserow.core.actions.registries import BaserowAction
from baserow.core.actions.scopes import RootScopeType
from baserow.core.trash.handler import TrashHandler

User = get_user_model()


class RestoreAction(BaserowAction["Params"]):
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
            scope=RootScopeType.value(),
        )

    @classmethod
    def redo(
        cls,
        user: User,
        params: "Params",
    ):
        TrashHandler.restore_item(
            user,
            params.trash_item_type,
            params.trash_item_id,
            parent_trash_item_id=params.parent_trash_item_id,
        )

    @classmethod
    def undo(cls, user: User, params: "Params"):
        # todo this is painful without a trash system which lets us delete just using
        # an id and a trash_item_type
        pass

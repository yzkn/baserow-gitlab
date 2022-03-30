import abc
import dataclasses
from typing import TypeVar, Generic, Any

from django.contrib.auth import get_user_model

from baserow.core.actions.models import Action
from baserow.core.actions.scopes import RootScope
from baserow.core.registry import Registry, Instance
from baserow.core.user.utils import UserType

User = get_user_model()


class BaserowActionRegistry(Registry):
    name = "action"


T = TypeVar("T")
K = TypeVar("K")


class BaserowAction(Instance, abc.ABC, Generic[T]):
    @property
    @abc.abstractmethod
    def type(self) -> str:
        pass

    @dataclasses.dataclass
    class Params:
        pass

    @classmethod
    @abc.abstractmethod
    def do(cls, *args, **kwargs) -> Any:
        pass

    @classmethod
    @abc.abstractmethod
    def undo(cls, user: UserType, params: T):
        pass

    @classmethod
    @abc.abstractmethod
    def redo(cls, user: UserType, params: T):
        pass

    @classmethod
    def register_action(
        cls,
        user: UserType,
        params: T,
        scope: RootScope,
    ):
        Action.objects.create(
            user=user,
            type=cls.type,
            params=params,
            scope=scope.scope,
            session=getattr(user, "undo_session", None),
        )


action_registry: BaserowActionRegistry = BaserowActionRegistry()

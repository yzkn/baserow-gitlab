import abc
import dataclasses
from typing import TypeVar, Generic, Any, Type, NewType

from django.contrib.auth import get_user_model
from rest_framework import serializers

from baserow.core.actions.models import Action
from baserow.core.registry import Registry, Instance
from baserow.core.user.sessions import get_untrusted_client_session_id
from baserow.core.user.utils import UserType

User = get_user_model()

Scope = NewType("Scope", str)


class ScopeType(abc.ABC, Instance):
    @property
    @abc.abstractmethod
    def type(self) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def value(cls, *args, **kwargs) -> Scope:
        pass

    @abc.abstractmethod
    def valid_serializer_value_to_scope_value(self, value) -> Scope:
        pass

    @abc.abstractmethod
    def get_request_serializer_field(self) -> serializers.Field:
        pass


class ActionScopeRegistry(Registry[ScopeType]):
    name = "action_scope"


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
    def undo(cls, user: UserType, params: T, action_being_undone: Action):
        pass

    @classmethod
    @abc.abstractmethod
    def redo(cls, user: UserType, params: T, action_being_redone: Action):
        pass

    @classmethod
    def register_action(
        cls,
        user: UserType,
        params: T,
        scope: Scope,
    ):
        session = get_untrusted_client_session_id(user)
        Action.objects.create(
            user=user,
            type=cls.type,
            params=params,
            scope=scope,
            session=session,
        )


action_scope_registry: ActionScopeRegistry = ActionScopeRegistry()
action_registry: BaserowActionRegistry = BaserowActionRegistry()

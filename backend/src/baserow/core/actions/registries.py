import abc
import dataclasses
from typing import TypeVar, Generic, Any, NewType

from rest_framework import serializers

from baserow.core.actions.models import Action
from baserow.core.registry import Registry, Instance
from baserow.core.user.sessions import get_untrusted_client_session_id
from baserow.core.user.utils import UserType

# An alias type of a str (its exactly a str, just with a different name in the type
# system). We use this instead of a normal str for type safety ensuring
# only str's returned by ActionCategoryType.value and
# ActionCategoryType.valid_serializer_value_to_category_str can be used in functions
# which are expecting an ActionCategoryStr.
ActionCategoryStr = NewType("Scope", str)


class ActionCategoryType(abc.ABC, Instance):
    """
    When a BaserowAction occurs we save a Action model in the database with a particular
    category. An ActionCategoryType is a possible type of category an action can be
    categorized into, ultimately represented by a string and stored in the db.

    For example, there is a GroupActionCategoryType. When stored in the database
    actions in this category have a category value of "group10", "group999", etc.
    """

    @property
    @abc.abstractmethod
    def type(self) -> str:
        """
        Implement this to be an unique name to identify this type of action category.
        """

        pass

    @classmethod
    @abc.abstractmethod
    def value(cls, *args, **kwargs) -> ActionCategoryStr:
        """
        Implement and use this method for constructing an ActionCategoryStr of this type
        programmatically. This should almost always be prefixed by cls.type to prevent
        categories of one type clashing with another.

        The args and kwargs should be completely overridden by the implemented type to
        accept whatever parameters are needed to construct a specific str for this
        category.

        For example an Action.do method will call this method
        to generate the category for an Action model instance it is saving.
        """

        pass

    @abc.abstractmethod
    def get_request_serializer_field(self) -> serializers.Field:
        """
        Implement this to return the DRF Field serializer which will be used to
        deserialize API requests including action categories. The deserialized value
        from API requests will then be provided to
        valid_serializer_value_to_category_str.
        """

        pass

    @abc.abstractmethod
    def valid_serializer_value_to_category_str(self, value: Any) -> ActionCategoryStr:
        """
        Implement this to return an ActionCategoryStr (an alias type for str) when
        given the valid value deserialized by get_request_serializer_field. The
        returned str will be used querying for actions by category.
        """

        pass


class ActionCategoryRegistry(Registry[ActionCategoryType]):
    name = "action_category"


class ActionTypeRegistry(Registry):
    name = "action"


T = TypeVar("T")
K = TypeVar("K")


class ActionType(Instance, abc.ABC, Generic[T]):
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
    def default_category(cls, *args, **kwargs) -> ActionCategoryStr:
        """
        Should return the default action category which actions of this type are stored
        in. Any args or kwargs specific to the action type can be provided in the
        overridden method.
        """

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
        category: ActionCategoryStr,
    ):
        session = get_untrusted_client_session_id(user)
        Action.objects.create(
            user=user,
            type=cls.type,
            params=params,
            category=category,
            session=session,
        )


action_category_registry: ActionCategoryRegistry = ActionCategoryRegistry()
action_type_registry: ActionTypeRegistry = ActionTypeRegistry()

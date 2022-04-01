from typing import cast

from rest_framework import serializers

from baserow.core.actions.registries import ScopeType, Scope


class RootScopeType(ScopeType):
    type = "root"

    @classmethod
    def value(cls) -> Scope:
        return cast(Scope, cls.type)

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.BooleanField(
            required=False,
            help_text="If set to true then actions registered in the root scope will "
            "be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_value(self, value) -> Scope:
        return self.value()


class GroupScopeType(ScopeType):
    type = "group"

    @classmethod
    def value(cls, group_id: int) -> Scope:
        return cast(Scope, cls.type + str(group_id))

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            required=False,
            help_text="If set to a groups id then any actions directly related to that "
            "group will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_value(self, value: int) -> Scope:
        return self.value(value)


class ApplicationScopeType(ScopeType):
    type = "application"

    @classmethod
    def value(cls, application_id: int) -> Scope:
        return cast(Scope, cls.type + str(application_id))

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            required=False,
            help_text="If set to an applications id then any actions directly related "
            "to that application will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_scope_value(self, value: int) -> Scope:
        return self.value(value)

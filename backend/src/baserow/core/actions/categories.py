from typing import cast

from rest_framework import serializers

from baserow.core.actions.registries import ActionCategoryType, ActionCategoryStr


class RootActionCategoryType(ActionCategoryType):
    type = "root"

    @classmethod
    def value(cls) -> ActionCategoryStr:
        return cast(ActionCategoryStr, cls.type)

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.BooleanField(
            allow_null=True,
            required=False,
            help_text="If set to true then actions registered in the root category "
            "will be included when undoing or redoing.",
        )

    def valid_serializer_value_to_category_str(self, value) -> ActionCategoryStr:
        return self.value()


class GroupActionCategoryType(ActionCategoryType):
    type = "group"

    @classmethod
    def value(cls, group_id: int) -> ActionCategoryStr:
        return cast(ActionCategoryStr, cls.type + str(group_id))

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            allow_null=True,
            required=False,
            help_text="If set to a groups id then any actions directly related to that "
            "group will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_category_str(self, value: int) -> ActionCategoryStr:
        return self.value(value)


class ApplicationActionCategoryType(ActionCategoryType):
    type = "application"

    @classmethod
    def value(cls, application_id: int) -> ActionCategoryStr:
        return cast(ActionCategoryStr, cls.type + str(application_id))

    def get_request_serializer_field(self) -> serializers.Field:
        return serializers.IntegerField(
            min_value=0,
            allow_null=True,
            required=False,
            help_text="If set to an applications id then any actions directly related "
            "to that application will be be included when undoing or redoing.",
        )

    def valid_serializer_value_to_category_str(self, value: int) -> ActionCategoryStr:
        return self.value(value)

from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from baserow.api.groups.invitations.serializers import UserGroupInvitationSerializer
from baserow.api.mixins import UnknownFieldRaisesExceptionSerializerMixin
from baserow.api.user.validators import password_validation, language_validation
from baserow.core.actions.models import Action
from baserow.core.actions.registries import action_category_registry, ActionCategoryStr
from baserow.core.models import Template, UserLogEntry
from baserow.core.user.utils import normalize_email_address

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    language = serializers.CharField(
        source="profile.language",
        required=False,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )

    class Meta:
        model = User
        fields = ("first_name", "username", "password", "is_staff", "id", "language")
        extra_kwargs = {
            "password": {"write_only": True},
            "is_staff": {"read_only": True},
            "id": {"read_only": True},
        }


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField(
        help_text="The email address is also going to be the username."
    )
    password = serializers.CharField(validators=[password_validation])
    language = serializers.CharField(
        required=False,
        default=settings.LANGUAGE_CODE,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )
    authenticate = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Indicates whether an authentication token should be generated and "
        "be included in the response.",
    )
    group_invitation_token = serializers.CharField(
        required=False,
        help_text="If provided and valid, the user accepts the group invitation and "
        "will have access to the group after signing up.",
    )
    template_id = serializers.PrimaryKeyRelatedField(
        required=False,
        default=None,
        queryset=Template.objects.all(),
        help_text="The id of the template that must be installed after creating the "
        "account. This only works if the `group_invitation_token` param is not "
        "provided.",
    )


def get_action_categories_request_serializer():
    attrs = {}

    for category_type in action_category_registry.get_all():
        attrs[category_type.type] = category_type.get_request_serializer_field()

    return type(
        "ActionCategoriesRequestSerializer",
        (serializers.Serializer, UnknownFieldRaisesExceptionSerializerMixin),
        attrs,
    )


ActionCategoriesSerializer = get_action_categories_request_serializer()


class UndoRedoRequestSerializer(serializers.Serializer):
    categories = ActionCategoriesSerializer(
        required=True,
        help_text="A JSON object with keys and values representing the various action "
        "categories to include when undoing or redoing. Every action in Baserow will "
        "be associated with a action category, when undoing/redoing only actions "
        "which match any of the provided category key:value pairs will included when "
        "this endpoint picks the next action to undo/redo.",
    )

    @property
    def data(self) -> List[ActionCategoryStr]:
        category_list = []
        for category_type_str, category_value in self.validated_data[
            "categories"
        ].items():
            if category_value:
                category_type = action_category_registry.get(category_type_str)
                category_list.append(
                    category_type.valid_serializer_value_to_category_str(category_value)
                )
        return category_list


class UndoRedoResponseSerializer(serializers.ModelSerializer):
    # Please keep code values in sync with
    # web-frontend/modules/core/utils/undoRedoConstants.js:UNDO_REDO_RESULT_CODES
    NOTHING_TO_DO = "NOTHING_TO_DO"
    SUCCESS = "SUCCESS"
    SKIPPED_DUE_TO_ERROR = "SKIPPED_DUE_TO_ERROR"

    result_code = serializers.SerializerMethodField(
        help_text=f"Indicates the result of the undo/redo operation. Will be "
        f"'{SUCCESS}' on success, '{NOTHING_TO_DO}' when "
        f"there is no action to undo/redo and "
        f"'{SKIPPED_DUE_TO_ERROR}' when the undo/redo failed due "
        f"to a conflict or error and was skipped over."
    )

    action_type = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        source="type",
        help_text="If an action was undone/redone/skipped due to an error this field "
        "will contain the type of the action that was undone/redone.",
    )
    action_category = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        source="category",
        help_text="If an action was undone/redone/skipped due to an error this field "
        "will contain the category of the action that was undone/redone.",
    )

    @extend_schema_field(OpenApiTypes.STR)
    def get_result(self, instance):
        if instance is None:
            return self.NOTHING_TO_DO
        elif instance.error:
            return self.SKIPPED_DUE_TO_ERROR
        else:
            return self.SUCCESS

    class Meta:
        model = Action
        fields = ("action_type", "action_category", "result")


class AccountSerializer(serializers.Serializer):
    """
    This serializer must be kept in sync with `UserSerializer`.
    """

    first_name = serializers.CharField(min_length=1, max_length=32)
    language = serializers.CharField(
        source="profile.language",
        required=False,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )


class SendResetPasswordEmailBodyValidationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="The email address of the user that has requested a password reset."
    )
    base_url = serializers.URLField(
        help_text="The base URL where the user can reset his password. The reset "
        "token is going to be appended to the base_url (base_url "
        "'/token')."
    )


class ResetPasswordBodyValidationSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(validators=[password_validation])


class ChangePasswordBodyValidationSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[password_validation])


class NormalizedEmailField(serializers.EmailField):
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return normalize_email_address(data)


class NormalizedEmailWebTokenSerializer(JSONWebTokenSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = NormalizedEmailField()

    def validate(self, attrs):
        """
        This serializer is only used by the ObtainJSONWebToken view which is only used
        to generate a new token. When that happens we want to update the user's last
        login timestamp.
        """

        # In the future, when migrating away from the JWT implementation, we want to
        # respond with machine readable error codes when authentication fails.
        validated_data = super().validate(attrs)

        user = validated_data["user"]
        if not user.is_active:
            msg = "User account is disabled."
            raise serializers.ValidationError(msg)

        update_last_login(None, user)
        UserLogEntry.objects.create(actor=user, action="SIGNED_IN")
        # Call the user_signed_in method for each plugin that is un the registry to
        # notify all plugins that a user has signed in.
        from baserow.core.registries import plugin_registry

        for plugin in plugin_registry.registry.values():
            plugin.user_signed_in(user)
        return validated_data


class DashboardSerializer(serializers.Serializer):
    group_invitations = UserGroupInvitationSerializer(many=True)

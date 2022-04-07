from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException


class UserNotFound(Exception):
    """Raised when a user with given parameters is not found."""


class UserAlreadyExist(Exception):
    """Raised when a user could not be created because the email already exists."""


class PasswordDoesNotMatchValidation(Exception):
    """Raised when the provided password does not match validation."""


class InvalidPassword(Exception):
    """Raised when the provided password is incorrect."""


class DisabledSignupError(Exception):
    """
    Raised when a user account is created when the new signup setting is disabled.
    """


class InvalidClientSessionIdAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "ERROR_INVALID_CLIENT_SESSION_ID"
    default_detail = (
        f"An invalid {settings.CLIENT_SESSION_ID_HEADER} header was provided. It must "
        f"be between 1 and {settings.MAX_CLIENT_SESSION_ID_LENGTH} characters long and "
        f"must only contain alphanumeric or the - characters.",
    )

import re
from typing import Any

from django.conf import settings

from baserow.core.user.exceptions import InvalidClientSessionIdAPIException
from baserow.core.user.utils import UserType

UNTRUSTED_CLIENT_SESSION_ID_USER_ATTR = "untrusted_client_session_id"


def raise_if_not_valid_untrusted_client_session_id(value: Any):
    is_valid = (
        isinstance(value, str)
        and re.match(r"^[0-9a-zA-Z-]+$", value)
        and len(value) <= settings.MAX_CLIENT_SESSION_ID_LENGTH
    )
    if is_valid:
        raise InvalidClientSessionIdAPIException()


def set_untrusted_client_session_id_from_request_or_raise_if_invalid(
    user: UserType, request
):
    # TODO figure out how to convert setting.CLIENT_SESSION_ID_HEADER to this value
    #      or get the header value using the setting value directly.
    session_id = request.META.get("HTTP_CLIENTSESSIONID", None)
    if session_id is not None:
        raise_if_not_valid_untrusted_client_session_id(session_id)
        set_untrusted_client_session_id(user, session_id)


def set_untrusted_client_session_id(user: UserType, session_id: str):
    setattr(user, UNTRUSTED_CLIENT_SESSION_ID_USER_ATTR, session_id)


def get_untrusted_client_session_id(user: UserType):
    return getattr(user, UNTRUSTED_CLIENT_SESSION_ID_USER_ATTR, None)

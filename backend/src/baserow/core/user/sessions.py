import re
from typing import Any

from baserow.core.user.utils import UserType

USER_SESSION_ID_ATTR = "session_id"


def valid_user_session_id(value: Any):
    return (
        value is not None
        and isinstance(value, str)
        and re.match(r"^[0-9a-z-]+$", value)
    )


def set_user_session_id_from_request(user: UserType, request):
    # TODO figure out how to share the magic string
    session_id = request.META.get("HTTP_SESSIONID", None)
    if valid_user_session_id(session_id):
        set_user_session_id(user, session_id)


def set_user_session_id(user: UserType, session_id: str):
    setattr(user, USER_SESSION_ID_ATTR, session_id)


def get_user_session_id(user: UserType):
    return getattr(user, USER_SESSION_ID_ATTR, None)

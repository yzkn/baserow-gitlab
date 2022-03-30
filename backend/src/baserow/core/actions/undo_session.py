import re
from typing import Any

from baserow.core.user.utils import UserType

UNDO_SESSION_USER_ATTR = "undo_session"
UNDO_SESSION_REQUEST_HEADER = "Session"


def valid_undo_session(value: Any):
    return (
        value is not None
        and isinstance(value, str)
        and re.match(r"^[0-9a-z-]+$", value)
    )


def set_undo_session(request):
    undo_session = request.META.get(UNDO_SESSION_REQUEST_HEADER, None)
    if valid_undo_session(undo_session):
        setattr(request.user, UNDO_SESSION_USER_ATTR, undo_session)


def get_undo_session(user: UserType):
    return getattr(user, UNDO_SESSION_USER_ATTR, None)

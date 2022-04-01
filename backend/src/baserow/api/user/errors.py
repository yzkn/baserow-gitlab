# None of these are passwords
from rest_framework.status import HTTP_400_BAD_REQUEST

ERROR_ALREADY_EXISTS = "ERROR_EMAIL_ALREADY_EXISTS"  # nosec
ERROR_USER_NOT_FOUND = "ERROR_USER_NOT_FOUND"  # nosec
ERROR_INVALID_OLD_PASSWORD = "ERROR_INVALID_OLD_PASSWORD"  # nosec
ERROR_DISABLED_SIGNUP = "ERROR_DISABLED_SIGNUP"  # nosec
ERROR_NO_MORE_ACTIONS_TO_UNDO = (
    "ERROR_NO_MORE_ACTIONS_TO_UNDO",
    HTTP_400_BAD_REQUEST,
    "There are no more actions to undo.",
)
ERROR_NO_MORE_ACTIONS_TO_REDO = (
    "ERROR_NO_MORE_ACTIONS_TO_REDO",
    HTTP_400_BAD_REQUEST,
    "There are no more actions to redo.",
)
ERROR_SKIPPING_UNDO_BECAUSE_IT_FAILED = (
    "ERROR_SKIPPING_UNDO_BECAUSE_IT_FAILED",
    HTTP_400_BAD_REQUEST,
    "Failed to undo the previous action, skipping over it.",
)
ERROR_SKIPPING_REDO_BECAUSE_IT_FAILED = (
    "ERROR_SKIPPING_REDO_BECAUSE_IT_FAILED",
    HTTP_400_BAD_REQUEST,
    "Failed to redo the previous action, skipping over it.",
)

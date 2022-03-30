import re

from baserow.core.actions.undo_session import valid_undo_session


class UndoSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        response = self.get_response(request)

        return response

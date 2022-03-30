from django.utils import timezone

from baserow.core.actions.exceptions import (
    NoMoreActionsToUndoException,
    NoMoreActionsToRedoException,
)
from baserow.core.actions.models import Action
from baserow.core.actions.registries import User, action_registry
from baserow.core.actions.scopes import RootScope


class ActionHandler:
    @classmethod
    def undo(cls, user: User, scope: RootScope, session: str):
        latest_not_undone_action_in_scope = (
            Action.objects.filter(user=user, undone_at__isnull=True, session=session)
            .filter(scope.scope_q)
            .order_by("-created_on", "-id")
            .select_for_update()
            .first()
        )
        if latest_not_undone_action_in_scope is None:
            raise NoMoreActionsToUndoException()
        action_type = action_registry.get(latest_not_undone_action_in_scope.type)
        latest_params = action_type.Params(**latest_not_undone_action_in_scope.params)
        try:
            action_type.undo(user, latest_params)
        finally:
            latest_not_undone_action_in_scope.undone_at = timezone.now()
            latest_not_undone_action_in_scope.save()

    @classmethod
    def redo(cls, user: User, scope: RootScope):
        latest_undone_action_in_scope = (
            Action.objects.filter(user=user, undone_at__isnull=False)
            .filter(scope.scope_q)
            .order_by("-undone_at", "-id")
            .select_for_update()
            .first()
        )

        # There have been no undoes
        if latest_undone_action_in_scope is None:
            raise NoMoreActionsToRedoException()

        normal_action_happened_since_undo = (
            Action.objects.filter(
                user=user,
                created_on__gt=latest_undone_action_in_scope.undone_at,
                undone_at__isnull=True,
            )
            .filter(scope.scope_q)
            .exists()
        )
        if normal_action_happened_since_undo:
            raise NoMoreActionsToRedoException()

        action_type = action_registry.get(latest_undone_action_in_scope.type)
        latest_params = action_type.Params(**latest_undone_action_in_scope.params)
        action_type.redo(user, latest_params)
        latest_undone_action_in_scope.undone_at = None
        latest_undone_action_in_scope.save()

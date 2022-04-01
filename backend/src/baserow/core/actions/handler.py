import logging
import traceback
from typing import List

from django.db.models import Q
from django.utils import timezone

from baserow.core.actions.exceptions import (
    NoMoreActionsToUndoException,
    NoMoreActionsToRedoException,
    SkippingRedoBecauseItFailedException,
    SkippingUndoBecauseItFailedException,
)
from baserow.core.actions.models import Action
from baserow.core.actions.registries import action_registry, Scope
from baserow.core.user.utils import UserType

logger = logging.getLogger(__name__)


def scopes_to_q_filter(scopes: List[Scope]):
    q = Q()
    for scope in scopes:
        q |= Q(scope=scope)
    return q


class ActionHandler:
    @classmethod
    def undo(cls, user: UserType, scopes: List[Scope], session: str):
        # TODO think of a nicer way realtime updates are sent to all when undo/redoing
        user.web_socket_id = None
        latest_not_undone_action_in_scope = (
            Action.objects.filter(user=user, undone_at__isnull=True, session=session)
            .filter(scopes_to_q_filter(scopes))
            .order_by("-created_on", "-id")
            .select_for_update()
            .first()
        )
        if latest_not_undone_action_in_scope is None:
            raise NoMoreActionsToUndoException()
        try:
            action_type = action_registry.get(latest_not_undone_action_in_scope.type)
            latest_params = action_type.Params(
                **latest_not_undone_action_in_scope.params
            )
            action_type.undo(user, latest_params)
        except Exception:
            tb = traceback.format_exc()
            logger.error(
                f"Undoing {latest_not_undone_action_in_scope} failed because of: \n{tb}"
            )
            latest_not_undone_action_in_scope.error = tb
            raise SkippingUndoBecauseItFailedException()
        finally:
            latest_not_undone_action_in_scope.undone_at = timezone.now()
            latest_not_undone_action_in_scope.save()

    @classmethod
    def redo(cls, user: UserType, scopes: List[Scope], session: str):
        # TODO think of a nicer way realtime updates are sent to all when undo/redoing
        user.web_socket_id = None
        scopes_filter = scopes_to_q_filter(scopes)
        latest_undone_action_in_scope = (
            Action.objects.filter(user=user, undone_at__isnull=False, session=session)
            .filter(scopes_filter)
            .order_by("-undone_at", "-id")
            .select_for_update()
            .first()
        )

        if latest_undone_action_in_scope is None:
            # There have been no undoes
            raise NoMoreActionsToRedoException()

        normal_action_happened_since_undo = (
            Action.objects.filter(
                user=user,
                created_on__gt=latest_undone_action_in_scope.undone_at,
                undone_at__isnull=True,
            )
            .filter(scopes_filter)
            .exists()
        )
        if normal_action_happened_since_undo:
            raise NoMoreActionsToRedoException()

        if latest_undone_action_in_scope.error:
            # We are redoing an undo action that failed and so we have nothing to redo
            # However we mark it as redone with no error so the user can try undo again
            # to see if it works this time.
            latest_undone_action_in_scope.undone_at = None
            latest_undone_action_in_scope.error = None
            latest_undone_action_in_scope.save()
            raise SkippingRedoBecauseItFailedException()

        try:
            action_type = action_registry.get(latest_undone_action_in_scope.type)
            latest_params = action_type.Params(**latest_undone_action_in_scope.params)
            action_type.redo(user, latest_params)
        except Exception:
            tb = traceback.format_exc()
            logger.error(
                f"Redoing {normal_action_happened_since_undo} failed because of: \n"
                f"{tb}",
            )
            latest_undone_action_in_scope.error = tb
            raise SkippingRedoBecauseItFailedException()
        finally:
            latest_undone_action_in_scope.undone_at = None
            latest_undone_action_in_scope.save()

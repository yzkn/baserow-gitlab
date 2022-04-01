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
from baserow.core.actions.registries import action_type_registry, ActionCategoryStr
from baserow.core.user.utils import UserType

logger = logging.getLogger(__name__)


def categories_list_to_q_filter(categories: List[ActionCategoryStr]):
    q = Q()
    for category_str in categories:
        q |= Q(category=category_str)
    return q


class ActionHandler:
    @classmethod
    def undo(cls, user: UserType, categories: List[ActionCategoryStr], session: str):
        # TODO think of a nicer way realtime updates are sent to all when undo/redoing
        user.web_socket_id = None
        latest_not_undone_action = (
            Action.objects.filter(user=user, undone_at__isnull=True, session=session)
            .filter(categories_list_to_q_filter(categories))
            .order_by("-created_on", "-id")
            .select_for_update()
            .first()
        )
        if latest_not_undone_action is None:
            raise NoMoreActionsToUndoException()

        action_being_undone = latest_not_undone_action
        try:
            action_type = action_type_registry.get(latest_not_undone_action.type)
            latest_params = action_type.Params(**latest_not_undone_action.params)
            action_type.undo(user, latest_params, action_being_undone)
        except Exception:
            tb = traceback.format_exc()
            logger.error(
                f"Undoing {latest_not_undone_action} failed because of: \n{tb}"
            )
            latest_not_undone_action.error = tb
            raise SkippingUndoBecauseItFailedException()
        finally:
            latest_not_undone_action.undone_at = timezone.now()
            latest_not_undone_action.save()

    @classmethod
    def redo(cls, user: UserType, categories: List[ActionCategoryStr], session: str):
        # TODO think of a nicer way realtime updates are sent to all when undo/redoing
        user.web_socket_id = None
        categories_filter = categories_list_to_q_filter(categories)
        latest_undone_action = (
            Action.objects.filter(user=user, undone_at__isnull=False, session=session)
            .filter(categories_filter)
            .order_by("-undone_at", "-id")
            .select_for_update()
            .first()
        )

        if latest_undone_action is None:
            # There have been no undoes
            raise NoMoreActionsToRedoException()

        normal_action_happened_since_undo = (
            Action.objects.filter(
                user=user,
                created_on__gt=latest_undone_action.undone_at,
                undone_at__isnull=True,
            )
            .filter(categories_filter)
            .exists()
        )
        if normal_action_happened_since_undo:
            raise NoMoreActionsToRedoException()

        if latest_undone_action.error:
            # We are redoing an undo action that failed and so we have nothing to redo
            # However we mark it as redone with no error so the user can try undo again
            # to see if it works this time.
            latest_undone_action.undone_at = None
            latest_undone_action.error = None
            latest_undone_action.save()
            raise SkippingRedoBecauseItFailedException()

        action_being_redone = latest_undone_action
        try:
            action_type = action_type_registry.get(latest_undone_action.type)
            latest_params = action_type.Params(**latest_undone_action.params)
            action_type.redo(user, latest_params, action_being_redone)
        except Exception:
            tb = traceback.format_exc()
            logger.error(
                f"Redoing {normal_action_happened_since_undo} failed because of: \n"
                f"{tb}",
            )
            latest_undone_action.error = tb
            raise SkippingRedoBecauseItFailedException()
        finally:
            latest_undone_action.undone_at = None
            latest_undone_action.save()

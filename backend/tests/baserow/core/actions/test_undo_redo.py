import pytest

from baserow.core.actions.handler import ActionHandler
from baserow.core.actions.models import Action
from baserow.core.actions.registries import (
    action_type_registry,
)
from baserow.core.actions.categories import (
    RootActionCategoryType,
)
from baserow.core.group_actions import CreateGroupActionType, UpdateGroupActionType
from baserow.core.models import Group
from baserow.core.utils import mark_as_locked


@pytest.mark.django_db
def test_can_undo_creating_group(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test"
    )
    group = group_user.group
    assert group.id is not None
    assert Action.objects.count() == 1
    create_group_action = Action.objects.order_by("id")[0]
    assert create_group_action.user == user
    assert create_group_action.category == "root"
    assert create_group_action.params == {
        "created_group_id": group.id,
        "group_name": "test",
    }
    assert create_group_action.undone_at is None

    ActionHandler.undo(user, [RootActionCategoryType.value()], session_id)

    assert Group.objects.filter(pk=group.id).count() == 0

    assert Action.objects.count() == 1
    undone_action = Action.objects.first()
    assert undone_action.user == user
    assert undone_action.category == "root"
    assert undone_action.params == {
        "created_group_id": group.id,
        "group_name": "test",
    }
    assert undone_action.undone_at is not None


@pytest.mark.django_db
def test_can_undo_redo_creating_group(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test"
    )
    group2_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test2"
    )
    group = group_user.group
    group2 = group2_user.group

    ActionHandler.undo(user, [RootActionCategoryType.value()], session_id)

    assert not Group.objects.filter(pk=group2.id).exists()

    assert Action.objects.count() == 2
    assert Action.objects.filter(undone_at__isnull=False).count() == 1
    assert (
        Action.objects.get(undone_at__isnull=False).params["created_group_id"]
        == group2.id
    )

    ActionHandler.redo(user, [RootActionCategoryType.value()], session_id)

    assert Group.objects.filter(pk=group2.id).exists()
    assert Action.objects.filter(undone_at__isnull=True).count() == 2


@pytest.mark.django_db
def test_can_undo_updating_group(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test"
    )

    updated_group = action_type_registry.get_by_type(UpdateGroupActionType).do(
        user, mark_as_locked(group_user.group), "new name"
    )

    assert updated_group.name == "new name"
    ActionHandler.undo(user, [RootActionCategoryType.value()], session_id)
    updated_group.refresh_from_db()
    assert updated_group.name == "test"

    assert Action.objects.count() == 2
    assert Action.objects.filter(undone_at__isnull=False).count() == 1

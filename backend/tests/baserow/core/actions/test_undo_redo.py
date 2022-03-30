import pytest

from baserow.core.actions.handler import ActionHandler
from baserow.core.actions.models import Action
from baserow.core.actions.registries import (
    action_registry,
)
from baserow.core.actions.scopes import RootScope, GroupActionScope
from baserow.core.group_actions import CreateGroupAction, UpdateGroupAction
from baserow.core.models import Group
from baserow.core.utils import mark_as_locked


@pytest.mark.django_db
def test_can_undo_creating_group(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()

    group = action_registry.get_by_type(CreateGroupAction).do(user, "test")
    assert group.id is not None
    assert Action.objects.count() == 1
    create_group_action = Action.objects.order_by("id")[0]
    assert create_group_action.user == user
    assert create_group_action.scope == "root"
    assert create_group_action.params == {
        "created_group_id": group.id,
        "group_name": "test",
    }
    assert create_group_action.undone_at is None

    # todo set a session
    ActionHandler.undo(user, GroupActionScope(group.id), None)

    assert Group.objects.filter(pk=group.id).count() == 0

    assert Action.objects.count() == 1
    undone_action = Action.objects.first()
    assert undone_action.user == user
    assert undone_action.scope == "root"
    assert undone_action.params == {
        "created_group_id": group.id,
        "group_name": "test",
    }
    assert undone_action.undone_at is not None


@pytest.mark.django_db
def test_can_undo_redo_creating_group(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()

    group = action_registry.get_by_type(CreateGroupAction).do(user, "test")
    group2 = action_registry.get_by_type(CreateGroupAction).do(user, "test2")

    # todo set sessions
    ActionHandler.undo(user, GroupActionScope(group.id), None)

    assert not Group.objects.filter(pk=group2.id).exists()

    assert Action.objects.count() == 2
    assert Action.objects.filter(undone_at__isnull=False).count() == 1

    ActionHandler.redo(user, RootScope())

    assert Group.objects.filter(pk=group2.id).exists()
    assert Action.objects.filter(undone_at__isnull=True).count() == 2


@pytest.mark.django_db
def test_can_undo_updating_group(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()

    group_user = action_registry.get_by_type(CreateGroupAction).do(user, "test")

    updated_group = action_registry.get_by_type(UpdateGroupAction).do(
        user, mark_as_locked(group_user.group), "new name"
    )

    assert updated_group.name == "new name"
    # todo set a session
    ActionHandler.undo(user, GroupActionScope(updated_group.id), None)
    updated_group.refresh_from_db()
    assert updated_group.name == "test"

    assert Action.objects.count() == 2
    assert Action.objects.filter(undone_at__isnull=False).count() == 1

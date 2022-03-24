import pytest

from baserow.core.models import Group
from baserow.core.undo.models import Action
from baserow.core.undo.undo1 import (
    CreateGroupAction,
    ActionHandler,
    GroupActionScope,
    RootScope,
)


@pytest.mark.django_db
def test_can_undo_creating_group(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()

    group = CreateGroupAction.create_group(user, "test", register_action=True)
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

    assert ActionHandler().undo(user, GroupActionScope(group.id))

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
def test_can_undo_creating_group(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()

    group = CreateGroupAction.create_group(user, "test", register_action=True)
    group2 = CreateGroupAction.create_group(user, "test2", register_action=True)

    assert ActionHandler().undo(user, GroupActionScope(group.id))

    assert not Group.objects.filter(pk=group2.id).exists()

    assert Action.objects.count() == 2
    assert Action.objects.filter(undone_at__isnull=False).count() == 1

    assert ActionHandler().redo(user, RootScope())

    assert Group.objects.filter(pk=group2.id).exists()
    assert Action.objects.filter(undone_at__isnull=True).count() == 2

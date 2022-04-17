import pytest
from baserow.contrib.database.views.actions import (
    CreateViewFilterActionType,
    DeleteViewFilterActionType,
    UpdateViewFilterActionType,
)
from baserow.contrib.database.views.models import ViewFilter

from baserow.core.action.scopes import (
    ApplicationActionScopeType,
)
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import (
    action_type_registry,
)


@pytest.mark.django_db
def test_can_undo_creating_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)

    view_filter = action_type_registry.get_by_type(CreateViewFilterActionType).do(
        grid_view.id,
        user,
        text_field.id,
        "equal",
        "",
    )

    ActionHandler.undo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    assert ViewFilter.objects.filter(pk=view_filter.id).count() == 0


@pytest.mark.django_db
def test_can_undo_redo_creating_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)

    view_filter = action_type_registry.get_by_type(CreateViewFilterActionType).do(
        grid_view.id,
        user,
        text_field.id,
        "equal",
        "",
    )

    ActionHandler.undo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    assert not ViewFilter.objects.filter(pk=view_filter.id).exists()

    ActionHandler.redo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    assert ViewFilter.objects.filter().count() == 1


@pytest.mark.django_db
def test_can_undo_updating_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )

    assert view_filter.value == "Test"
    assert view_filter.type == "equal"

    action_type_registry.get_by_type(UpdateViewFilterActionType).do(
        user,
        view_filter,
        filter_value="My new test value",
    )
    action_type_registry.get_by_type(UpdateViewFilterActionType).do(
        user,
        view_filter,
        filter_type="contains",
    )

    view_filter.refresh_from_db()
    assert view_filter.value == "My new test value"
    assert view_filter.type == "contains"

    ActionHandler.undo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    view_filter.refresh_from_db()
    assert view_filter.value == "My new test value"
    assert view_filter.type == "equal"

    ActionHandler.undo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    view_filter.refresh_from_db()
    assert view_filter.value == "Test"
    assert view_filter.type == "equal"


@pytest.mark.django_db
def test_can_undo_redo_updating_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )

    assert view_filter.value == "Test"

    action_type_registry.get_by_type(UpdateViewFilterActionType).do(
        user,
        view_filter,
        filter_value="My new test value",
    )

    view_filter.refresh_from_db()
    assert view_filter.value == "My new test value"

    ActionHandler.undo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    view_filter.refresh_from_db()
    assert view_filter.value == "Test"

    ActionHandler.redo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    view_filter.refresh_from_db()
    assert view_filter.value == "My new test value"


@pytest.mark.django_db
def test_can_undo_deleting_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )

    assert ViewFilter.objects.count() == 1

    action_type_registry.get_by_type(DeleteViewFilterActionType).do(
        user, view_filter.id
    )

    assert ViewFilter.objects.count() == 0

    ActionHandler.undo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    assert ViewFilter.objects.count() == 1


@pytest.mark.django_db
def test_can_undo_redo_deleting_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )

    assert ViewFilter.objects.count() == 1

    action_type_registry.get_by_type(DeleteViewFilterActionType).do(
        user, view_filter.id
    )

    assert ViewFilter.objects.count() == 0

    ActionHandler.undo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    assert ViewFilter.objects.count() == 1

    ActionHandler.redo(user, [ApplicationActionScopeType.value(table.id)], session_id)

    assert ViewFilter.objects.count() == 0

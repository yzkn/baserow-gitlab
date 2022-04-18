import pytest
from baserow.contrib.database.views.actions import CreateViewSortActionType
from baserow.contrib.database.views.models import ViewSort
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import ApplicationActionScopeType


@pytest.mark.django_db
def test_can_undo_creating_view_sort(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    number_field = data_fixture.create_number_field(
        table=table, name="value", number_decimal_places=1
    )

    assert ViewSort.objects.count() == 0

    action_type_registry.get_by_type(CreateViewSortActionType).do(
        user, grid_view.id, number_field.id, "DESC"
    )

    assert ViewSort.objects.count() == 1
    view_sort = ViewSort.objects.first()
    assert view_sort.view.id == grid_view.id
    assert view_sort.field.id == number_field.id
    assert view_sort.order == "DESC"

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(table.database.id)], session_id
    )

    assert ViewSort.objects.count() == 0


@pytest.mark.django_db
def test_can_undo_redo_creating_view_sort(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    number_field = data_fixture.create_number_field(
        table=table, name="value", number_decimal_places=1
    )

    assert ViewSort.objects.count() == 0

    action_type_registry.get_by_type(CreateViewSortActionType).do(
        user, grid_view.id, number_field.id, "DESC"
    )

    assert ViewSort.objects.count() == 1
    view_sort = ViewSort.objects.first()
    assert view_sort.view.id == grid_view.id
    assert view_sort.field.id == number_field.id
    assert view_sort.order == "DESC"

    ActionHandler.undo(
        user, [ApplicationActionScopeType.value(table.database.id)], session_id
    )

    assert ViewSort.objects.count() == 0

    ActionHandler.redo(
        user, [ApplicationActionScopeType.value(table.database.id)], session_id
    )

    assert ViewSort.objects.count() == 1
    ViewSort.objects.first()
    assert view_sort.view.id == grid_view.id
    assert view_sort.field.id == number_field.id
    assert view_sort.order == "DESC"

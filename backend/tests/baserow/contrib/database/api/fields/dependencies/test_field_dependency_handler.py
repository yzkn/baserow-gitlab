import pytest
from django.conf import settings

from baserow.contrib.database.fields.dependencies.circular_reference_checker import (
    will_cause_circular_dep,
)
from baserow.contrib.database.fields.dependencies.handler import FieldDependencyHandler
from baserow.contrib.database.fields.dependencies.models import (
    FieldDependency,
)
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.handler import FieldHandler


@pytest.mark.django_db
def test_deep_circular_ref(data_fixture, django_assert_num_queries):
    depth = settings.MAX_FIELD_REFERENCE_DEPTH
    starting_field = data_fixture.create_text_field()
    previous_field = starting_field
    for i in range(depth):
        new_field = data_fixture.create_text_field(table=starting_field.table)
        FieldDependency.objects.create(dependant=previous_field, dependency=new_field)
        previous_field = new_field

    with django_assert_num_queries(1):
        assert will_cause_circular_dep(previous_field, starting_field)
    with django_assert_num_queries(1):
        assert not will_cause_circular_dep(starting_field, previous_field)


@pytest.mark.django_db
def test_get_same_table_deps(data_fixture):
    field_a = data_fixture.create_text_field()
    field_b = data_fixture.create_text_field(table=field_a.table)
    field_c = data_fixture.create_text_field(table=field_a.table)
    field_in_other_table = data_fixture.create_text_field()
    FieldDependency.objects.create(dependant=field_a, dependency=field_b)
    FieldDependency.objects.create(dependant=field_b, dependency=field_c)
    FieldDependency.objects.create(dependant=field_c, dependency=field_in_other_table)
    assert FieldDependencyHandler().get_same_table_dependencies(field_a) == [field_b]
    assert FieldDependencyHandler().get_same_table_dependencies(field_b) == [field_c]
    assert FieldDependencyHandler().get_same_table_dependencies(field_c) == []


def when_field_updated(field, via=None, relation_changed=True):
    result = []
    for (
        dependant_field,
        dependant_field_type,
        via_path_to_starting_table,
    ) in field.dependant_fields_with_types(
        field_cache=FieldCache(),
        starting_via_path_to_starting_table=via,
        associated_relation_changed=relation_changed,
    ):
        if via_path_to_starting_table is None:
            via_path_to_starting_table = []
        result_dict = {
            "field": dependant_field,
            "via": via_path_to_starting_table,
        }
        then = when_field_updated(
            dependant_field, via=via_path_to_starting_table, relation_changed=False
        )
        if then:
            result_dict["then"] = then
        result.append(result_dict)
    return result


@pytest.mark.django_db
def test_dependencies_for_primary_lookup(data_fixture):
    user = data_fixture.create_user()
    table_a, table_b, table_a_link_field = data_fixture.create_two_linked_tables(
        user=user
    )

    table_a_primary = table_a.field_set.get(primary=True)
    table_b_link_field = table_a_link_field.link_row_related_field

    table_b_primary = table_b.field_set.get(primary=True)
    FieldHandler().update_field(
        user,
        table_a_primary.specific,
        new_type_name="formula",
        formula=f"lookup('{table_a_link_field.name}', '{table_b_primary.name}')",
    )

    assert when_field_updated(table_b_primary) == causes(
        a_field_update_for(table_a_link_field, via=[table_a_link_field]),
        a_field_update_for(
            table_a_primary.specific,
            via=[table_a_link_field],
            then=causes(
                a_field_update_for(
                    table_b_link_field,
                    via=[table_a_link_field, table_b_link_field],
                )
            ),
        ),
    )
    assert when_field_updated(table_a_primary) == causes(
        a_field_update_for(table_b_link_field, via=[table_b_link_field]),
    )
    assert when_field_updated(table_b_link_field) == causes(
        a_field_update_for(table_a_link_field, via=[table_a_link_field]),
        a_field_update_for(
            table_a_primary.specific,
            via=[table_a_link_field],
            then=causes(
                a_field_update_for(
                    table_b_link_field,
                    via=[table_a_link_field, table_b_link_field],
                )
            ),
        ),
    )

    assert when_field_updated(table_a_link_field) == causes(
        a_field_update_for(table_b_link_field, via=[table_b_link_field]),
        a_field_update_for(
            table_a_primary.specific,
            via=[],
            then=causes(
                a_field_update_for(
                    table_b_link_field,
                    via=[table_b_link_field],
                )
            ),
        ),
    )


@pytest.mark.django_db
def test_dependencies_for_triple_lookup(data_fixture):
    user = data_fixture.create_user()
    table_a, table_b, table_a_to_b_link_field = data_fixture.create_two_linked_tables(
        user=user
    )
    table_c, _, table_c_to_b_link_field = data_fixture.create_two_linked_tables(
        user=user, table_b=table_b
    )

    table_a_primary = table_a.field_set.get(primary=True).specific
    table_b_to_a_link_field = table_a_to_b_link_field.link_row_related_field
    table_b_to_c_link_field = table_c_to_b_link_field.link_row_related_field

    table_b_primary = table_b.field_set.get(primary=True).specific
    table_c_primary = table_c.field_set.get(primary=True).specific

    lookup_of_linked_field = FieldHandler().create_field(
        user,
        table=table_a,
        type_name="formula",
        name="lookup_of_link_field",
        formula=f"lookup('{table_a_to_b_link_field.name}', "
        f"'{table_b_to_c_link_field.name}')",
    )
    assert lookup_of_linked_field.error is None

    assert when_field_updated(table_c_primary) == causes(
        a_field_update_for(
            table_b_to_c_link_field,
            via=[table_b_to_c_link_field],
            then=causes(
                a_field_update_for(
                    lookup_of_linked_field,
                    via=[table_b_to_c_link_field, table_a_to_b_link_field],
                )
            ),
        )
    )
    assert when_field_updated(table_b_to_c_link_field) == causes(
        a_field_update_for(
            table_c_to_b_link_field,
            via=[table_c_to_b_link_field],
        ),
        a_field_update_for(
            lookup_of_linked_field,
            via=[table_a_to_b_link_field],
        ),
    )


def causes(*result):
    return list(result)


def a_field_update_for(field, via, then=None):
    r = {
        "field": field,
        "via": via,
    }
    if then:
        r["then"] = then
    return r

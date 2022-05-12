import pytest

from baserow.contrib.database.fields.dependencies.models import FieldDependency
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.handler import FieldDependencyHandler
from baserow.contrib.database.fields.registries import field_type_registry


@pytest.mark.django_db
def test_get_dependant_fields_with_type(data_fixture):
    table = data_fixture.create_database_table()
    text_field_1 = data_fixture.create_text_field(table=table)
    text_field_2 = data_fixture.create_text_field(table=table)
    text_field_3 = data_fixture.create_text_field(table=table)

    text_field_1_dependency_1 = data_fixture.create_text_field(table=table)
    text_field_1_dependency_2 = data_fixture.create_text_field(table=table)

    text_field_2_dependency_1 = data_fixture.create_text_field(table=table)
    text_field_2_dependency_2 = data_fixture.create_text_field(table=table)
    text_field_2_dependency_3 = data_fixture.create_text_field(table=table)

    link_field_to_table = data_fixture.create_link_row_field(link_row_table=table)
    text_field_1_and_2_dependency_1 = data_fixture.create_text_field(table=table)
    other_table_field = data_fixture.create_text_field(
        table=link_field_to_table.link_row_table
    )

    FieldDependency.objects.create(
        dependency=text_field_1, dependant=text_field_1_dependency_1
    )
    FieldDependency.objects.create(
        dependency=text_field_1, dependant=text_field_1_dependency_2
    )
    FieldDependency.objects.create(
        dependency=text_field_1, dependant=text_field_1_and_2_dependency_1
    )

    FieldDependency.objects.create(
        dependency=text_field_2, dependant=text_field_2_dependency_1
    )
    FieldDependency.objects.create(
        dependency=text_field_2,
        dependant=other_table_field,
        via=link_field_to_table,
    )
    FieldDependency.objects.create(
        dependency=text_field_2, dependant=text_field_2_dependency_3
    )
    FieldDependency.objects.create(
        dependency=text_field_2, dependant=text_field_1_and_2_dependency_1
    )

    field_cache = FieldCache()
    text_field_type = field_type_registry.get_by_model(text_field_1_dependency_1)

    results = FieldDependencyHandler.get_dependant_fields_with_type(
        field_ids=[text_field_1.id],
        associated_relations_changed=True,
        field_cache=field_cache,
    )
    expected_text_field_1_dependants = [
        (text_field_1_dependency_1, text_field_type, None),
        (text_field_1_dependency_2, text_field_type, None),
        (text_field_1_and_2_dependency_1, text_field_type, None),
    ]
    assert results == expected_text_field_1_dependants

    results = FieldDependencyHandler.get_dependant_fields_with_type(
        field_ids=[text_field_2.id],
        associated_relations_changed=True,
        field_cache=field_cache,
    )
    expected_text_field_2_dependants = [
        (text_field_2_dependency_1, text_field_type, None),
        (other_table_field, text_field_type, [link_field_to_table]),
        (
            text_field_2_dependency_3,
            text_field_type,
            None,
        ),
        (text_field_1_and_2_dependency_1, text_field_type, None),
    ]
    assert results == expected_text_field_2_dependants

    results = FieldDependencyHandler.get_dependant_fields_with_type(
        field_ids=[text_field_3.id],
        associated_relations_changed=True,
        field_cache=field_cache,
    )
    assert len(results) == 0

    results = FieldDependencyHandler.get_dependant_fields_with_type(
        field_ids=[text_field_1.id, text_field_2.id, text_field_3.id],
        associated_relations_changed=True,
        field_cache=field_cache,
    )
    assert (
        results == expected_text_field_1_dependants + expected_text_field_2_dependants
    )

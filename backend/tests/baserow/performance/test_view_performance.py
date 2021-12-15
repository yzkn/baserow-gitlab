from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from pyinstrument import Profiler
from rest_framework.status import HTTP_200_OK

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.management.commands.fill_table import fill_table
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.view_filters import EqualViewFilterType
from baserow.core.trash.handler import TrashHandler
from baserow.test_utils.helpers import setup_interesting_test_table


@pytest.mark.django_db
@pytest.mark.slow
# You must add --runslow -s to pytest to run this test, you can do this in intellij by
# editing the run config for this test and adding --runslow -s to additional args.
def test_adding_a_formula_field_compared_to_normal_field_isnt_slow(
    data_fixture, django_capture_on_commit_callbacks
):

    table, user, row, _ = setup_interesting_test_table(data_fixture)
    count = 10000
    fill_table(count, table)

    for i in range(10):
        grid_view = data_fixture.create_grid_view(user=user, table=table, public=True)
        for field in table.field_set.all():
            if EqualViewFilterType().field_is_compatible(field):
                for v in range(10):
                    data_fixture.create_view_filter(
                        user=user,
                        view=grid_view,
                        field=field,
                        value=f"test{v}",
                    )

    profiler = Profiler()
    profiler.start()
    with django_capture_on_commit_callbacks(execute=True):
        RowHandler().create_row(user=user, table=table, values={})
    profiler.stop()
    print("--------- Adding a normal field! -------")
    print(profiler.output_text(unicode=True, color=True))

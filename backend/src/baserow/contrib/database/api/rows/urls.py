from django.urls import re_path

from .views import RowsView, RowView, RowMoveView, RowsBatchCreateView


app_name = "baserow.contrib.database.api.rows"

urlpatterns = [
    re_path(r"table/(?P<table_id>[0-9]+)/$", RowsView.as_view(), name="list"),
    re_path(
        r"table/(?P<table_id>[0-9]+)/batch/$",
        RowsBatchCreateView.as_view(),
        name="bulk-create",
    ),
    re_path(
        r"table/(?P<table_id>[0-9]+)/(?P<row_id>[0-9]+)/$",
        RowView.as_view(),
        name="item",
    ),
    re_path(
        r"table/(?P<table_id>[0-9]+)/(?P<row_id>[0-9]+)/move/$",
        RowMoveView.as_view(),
        name="move",
    ),
]

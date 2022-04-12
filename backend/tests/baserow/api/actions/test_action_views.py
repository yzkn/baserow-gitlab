import pytest

from django.contrib.auth import get_user_model
from django.shortcuts import reverse

from baserow.api.user.serializers import UndoRedoResultCodeField

User = get_user_model()


@pytest.mark.django_db
def test_action(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    response = api_client.patch(
        reverse("api:user:undo"),
        {"scopes": {}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_CLIENTSESSIONID="test",
    )
    assert response.json() == {
        "action_scope": "",
        "action_type": "",
        "result_code": UndoRedoResultCodeField.NOTHING_TO_DO,
    }

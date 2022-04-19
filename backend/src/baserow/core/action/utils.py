import json

from typing import Any

from django.core.serializers.json import DjangoJSONEncoder


def params_dumps(data: Any) -> str:
    return json.dumps(data, cls=DjangoJSONEncoder)


def params_loads(data: str) -> Any:
    return json.loads(data)

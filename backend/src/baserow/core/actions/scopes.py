from django.db.models import Q


class RootScope:
    scope_list = ["root"]

    @property
    def scope(self):
        return ".".join(self.scope_list)

    @property
    def scope_q(self):
        q = Q()
        combined_scopes = []
        for scope in self.scope_list:
            combined_scopes.append(scope)
            q |= Q(scope=".".join(combined_scopes))

        return q


class GroupActionScope(RootScope):
    def __init__(self, group_pk: int):
        self.scope_list = super().scope_list + [f"group{group_pk}"]


class TableScope(GroupActionScope):
    def __init__(self, table):
        super().__init__(table.group_id)
        self.scope_list = super().scope_list + [f"table{table.id}"]

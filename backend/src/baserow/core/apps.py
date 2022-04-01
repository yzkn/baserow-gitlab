from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "baserow.core"

    def ready(self):
        from baserow.core.trash.registries import trash_item_type_registry
        from baserow.core.actions.registries import (
            action_registry,
            action_scope_registry,
        )
        from baserow.core.trash.trash_types import GroupTrashableItemType
        from baserow.core.trash.trash_types import ApplicationTrashableItemType
        from baserow.core.group_actions import CreateGroupAction

        trash_item_type_registry.register(GroupTrashableItemType())
        trash_item_type_registry.register(ApplicationTrashableItemType())

        from baserow.core.group_actions import (
            UpdateGroupAction,
            DeleteGroupAction,
        )
        from baserow.core.trash.actions import RestoreAction

        action_registry.register(CreateGroupAction())
        action_registry.register(DeleteGroupAction())
        action_registry.register(UpdateGroupAction())
        action_registry.register(RestoreAction())

        from baserow.core.actions.scopes import RootScopeType, GroupScopeType

        action_scope_registry.register(RootScopeType())
        action_scope_registry.register(GroupScopeType())

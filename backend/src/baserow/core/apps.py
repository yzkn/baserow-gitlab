from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "baserow.core"

    def ready(self):
        from baserow.core.trash.registries import trash_item_type_registry
        from baserow.core.actions.registries import (
            action_type_registry,
            action_scope_registry,
        )
        from baserow.core.trash.trash_types import GroupTrashableItemType
        from baserow.core.trash.trash_types import ApplicationTrashableItemType

        trash_item_type_registry.register(GroupTrashableItemType())
        trash_item_type_registry.register(ApplicationTrashableItemType())

        from baserow.core.actions.group_actions import (
            CreateGroupActionType,
            UpdateGroupActionType,
            DeleteGroupActionType,
        )

        action_type_registry.register(CreateGroupActionType())
        action_type_registry.register(DeleteGroupActionType())
        action_type_registry.register(UpdateGroupActionType())

        from baserow.core.actions.scopes import (
            RootActionScopeType,
            GroupActionScopeType,
            ApplicationActionScopeType,
        )

        action_scope_registry.register(RootActionScopeType())
        action_scope_registry.register(GroupActionScopeType())
        action_scope_registry.register(ApplicationActionScopeType())

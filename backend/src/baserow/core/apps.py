from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "baserow.core"

    def ready(self):
        from baserow.core.trash.registries import trash_item_type_registry
        from baserow.core.actions.registries import (
            action_type_registry,
            action_category_registry,
        )
        from baserow.core.trash.trash_types import GroupTrashableItemType
        from baserow.core.trash.trash_types import ApplicationTrashableItemType
        from baserow.core.group_actions import CreateGroupActionType

        trash_item_type_registry.register(GroupTrashableItemType())
        trash_item_type_registry.register(ApplicationTrashableItemType())

        from baserow.core.group_actions import (
            UpdateGroupActionType,
            DeleteGroupActionType,
        )
        from baserow.core.trash.actions import RestoreActionType

        action_type_registry.register(CreateGroupActionType())
        action_type_registry.register(DeleteGroupActionType())
        action_type_registry.register(UpdateGroupActionType())
        action_type_registry.register(RestoreActionType())

        from baserow.core.actions.categories import (
            RootActionCategoryType,
            GroupActionCategoryType,
            ApplicationActionCategoryType,
        )

        action_category_registry.register(RootActionCategoryType())
        action_category_registry.register(GroupActionCategoryType())
        action_category_registry.register(ApplicationActionCategoryType())

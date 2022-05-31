from abc import ABC, abstractmethod

from baserow.core.registry import Registry, Instance


class GroupStorageUsageItemType(Instance, ABC):
    """
    A UsageItemType defines an item that can calcualte
    the usage of a group in a specific part of the application
    """

    @abstractmethod
    def calculate_storage_usage(self, group_id: int) -> int:
        """
        Calculates the storage usage of files for a group
        in a specific part of the application
        :param group_id: the group that the usage is calculated for
        :return: the total usage
        """

        pass


class GroupStorageUsageItemTypeRegistry(Registry):
    """
    A trash_item_type_registry contains all the different usage calcualtions
    that should be called when the total usage of a group is
    calculated
    """

    name = "usage"


group_storage_usage_item_registry = GroupStorageUsageItemTypeRegistry()

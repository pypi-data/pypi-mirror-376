"""
Folder managers for the Konigle SDK.

This module provides managers for folder resources, enabling hierarchical
content organization and management.
"""

from typing import cast

from konigle.filters.website import FolderFilters
from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.website.folder import Folder, FolderCreate, FolderUpdate


class BaseFolderManager:
    resource_class = Folder
    """The resource model class this manager handles."""

    resource_update_class = FolderUpdate
    """The model class used for updating resources."""

    base_path = "/content-folders"
    """The API base path for this resource type."""

    filter_class = FolderFilters
    """The filter model class for this resource type."""


class FolderManager(BaseFolderManager, BaseSyncManager):
    """Manager for folder resources."""

    def create(self, data: FolderCreate) -> Folder:
        """Create a new folder."""
        return cast(Folder, super().create(data))

    def update(self, id_: str, data: FolderUpdate) -> Folder:
        """Update an existing folder."""
        return cast(Folder, super().update(id_, data))


class AsyncFolderManager(BaseFolderManager, BaseAsyncManager):
    """Async manager for folder resources."""

    async def create(self, data: FolderCreate) -> Folder:
        """Create a new folder."""
        return cast(Folder, await super().create(data))

    async def update(self, id_: str, data: FolderUpdate) -> Folder:
        """Update an existing folder."""
        return cast(Folder, await super().update(id_, data))

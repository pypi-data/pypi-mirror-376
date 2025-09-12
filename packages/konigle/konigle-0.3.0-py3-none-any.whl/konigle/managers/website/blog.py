"""
Blog managers for the Konigle SDK.

This module provides managers for blog resources, enabling blog post
content management and operations.
"""

from typing import cast

from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.base import BaseResource
from konigle.models.website.blog import Blog, BlogCreate, BlogUpdate


class BaseBlogManager:
    resource_class = Blog
    """The resource model class this manager handles."""

    resource_update_class = BlogUpdate
    """The model class used for updating resources."""

    base_path = "/blogs"
    """The API base path for this resource type."""


class BlogManager(BaseBlogManager, BaseSyncManager):
    """Manager for blog resources."""

    def create(self, data: BlogCreate) -> Blog:
        """Create a new blog post."""
        return cast(Blog, super().create(data))

    def update(self, id_: str, data: BlogUpdate) -> Blog:
        """Update an existing blog post."""
        return cast(Blog, super().update(id_, data))

    def get(self, id_: str) -> Blog:
        return cast(Blog, super().get(id_))


class AsyncBlogManager(BaseBlogManager, BaseAsyncManager):
    """Async manager for blog resources."""

    async def create(self, data: BlogCreate) -> Blog:
        """Create a new blog post."""
        return cast(Blog, await super().create(data))

    async def update(self, id_: str, data: BlogUpdate) -> Blog:
        """Update an existing blog post."""
        return cast(Blog, await super().update(id_, data))

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SEOMeta(BaseModel):
    """SEO metadata for web pages - folder, page, blog etc."""

    title: str = Field(
        default="",
        title="SEO Title",
        description="Title for SEO purposes, max 70 characters",
    )
    """Title for SEO purposes, max 70 characters"""

    description: str = Field(
        default="",
        title="SEO Description",
        description="Description for SEO purposes, max 160 characters",
    )
    """Description for SEO purposes, max 160 characters"""

    keywords: str = Field(
        default="",
        title="SEO Keywords",
        description="Comma-separated keywords for SEO",
    )
    """Comma-separated keywords for SEO"""

    og_title: str = Field(
        default="",
        title="Open Graph Title",
        description="Title for social sharing, max 70 characters",
    )
    """Title for social sharing, max 70 characters"""

    og_description: str = Field(
        default="",
        title="Open Graph Description",
        description="Description for social sharing, max 160 characters",
    )
    """Description for social sharing, max 160 characters"""

    og_image: Optional[str] = Field(
        None,
        title="Open Graph Image URL",
        description="URL of the image for social sharing",
    )
    """URL of the image for social sharing"""

    model_config = ConfigDict(extra="ignore")

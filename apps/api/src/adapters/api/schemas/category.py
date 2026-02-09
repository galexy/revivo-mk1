"""Pydantic schemas for Category API endpoints.

Provides request/response schemas for Category CRUD operations.
Supports hierarchical categories with optional parent and tree structure views.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateCategoryRequest(BaseModel):
    """Request to create a new category."""

    name: str = Field(..., min_length=1, max_length=255)
    parent_id: str | None = Field(
        default=None, description="Parent category ID for subcategories"
    )
    icon: str | None = Field(
        default=None, max_length=50, description="Emoji or icon name"
    )
    category_type: str = Field(
        default="expense",
        pattern="^(income|expense)$",
        description="Category type: 'income' or 'expense'",
    )


class UpdateCategoryRequest(BaseModel):
    """Request to update a category."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    parent_id: str | None = Field(
        default=None, description="New parent ID (or null for top-level)"
    )
    icon: str | None = Field(default=None, max_length=50)


class CategoryResponse(BaseModel):
    """Response schema for a category."""

    id: str
    user_id: str
    name: str
    parent_id: str | None
    category_type: str  # "income" or "expense"
    is_system: bool
    is_hidden: bool
    sort_order: int
    icon: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    """Response for listing categories."""

    categories: list[CategoryResponse]
    total: int


class CategoryTreeResponse(BaseModel):
    """Response for category tree structure."""

    root: list[CategoryResponse]
    children: dict[str, list[CategoryResponse]]

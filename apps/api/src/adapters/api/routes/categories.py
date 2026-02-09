"""Category API endpoints.

Provides REST endpoints for category management:
- POST /categories - Create category with optional parent
- GET /categories - List all categories
- GET /categories/tree - Get hierarchical tree structure
- GET /categories/{id} - Get single category
- PATCH /categories/{id} - Update category
- DELETE /categories/{id} - Delete category (with optional reassignment)

All endpoints use dependency injection for CategoryService and current user.
Routes are protected by JWT authentication via get_current_user dependency.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from domain.model.category import Category, CategoryType
from domain.model.entity_id import CategoryId
from src.adapters.api.dependencies import (
    CurrentUser,
    get_category_service,
    get_current_user,
)
from src.adapters.api.schemas.category import (
    CategoryListResponse,
    CategoryResponse,
    CategoryTreeResponse,
    CreateCategoryRequest,
    UpdateCategoryRequest,
)
from src.application.services.category_service import CategoryError, CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])

# Type alias for cleaner signatures
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def _category_to_response(category: Category) -> CategoryResponse:
    """Convert domain Category to response schema."""
    return CategoryResponse(
        id=str(category.id),
        user_id=str(category.user_id),
        name=category.name,
        parent_id=str(category.parent_id) if category.parent_id else None,
        category_type=str(category.category_type),
        is_system=category.is_system,
        is_hidden=category.is_hidden,
        sort_order=category.sort_order,
        icon=category.icon,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CreateCategoryRequest,
    service: CategoryService = Depends(get_category_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CategoryResponse:
    """Create a new category."""
    parent_id = CategoryId.from_string(request.parent_id) if request.parent_id else None
    category_type = CategoryType(request.category_type)

    result = await service.create_category(
        user_id=current_user.user_id,
        name=request.name,
        parent_id=parent_id,
        icon=request.icon,
        category_type=category_type,
        household_id=current_user.household_id,
    )

    if isinstance(result, CategoryError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": result.code, "message": result.message},
        )

    return _category_to_response(result)


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    service: CategoryService = Depends(get_category_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CategoryListResponse:
    """List all categories for the current user."""
    user_id = current_user.user_id

    # Ensure system categories exist
    await service.ensure_system_categories(
        user_id, household_id=current_user.household_id
    )

    categories = service.get_user_categories(user_id)
    return CategoryListResponse(
        categories=[_category_to_response(c) for c in categories],
        total=len(categories),
    )


@router.get("/tree", response_model=CategoryTreeResponse)
async def get_category_tree(
    service: CategoryService = Depends(get_category_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CategoryTreeResponse:
    """Get categories organized as a tree structure."""
    user_id = current_user.user_id

    await service.ensure_system_categories(
        user_id, household_id=current_user.household_id
    )
    tree: dict[str, list[Category] | dict[str, list[Category]]] = (
        service.get_category_tree(user_id)
    )
    root_categories: list[Category] = tree["root"]  # type: ignore[assignment]  # dict value is list[Category]
    children_map: dict[str, list[Category]] = tree["children"]  # type: ignore[assignment]  # dict value is dict[str, list[Category]]

    return CategoryTreeResponse(
        root=[_category_to_response(c) for c in root_categories],
        children={
            parent_id: [_category_to_response(c) for c in children]
            for parent_id, children in children_map.items()
        },
    )


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CategoryResponse:
    """Get a category by ID."""
    cat_id = CategoryId.from_string(category_id)
    category = service.get_category(cat_id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    if category.user_id != current_user.user_id:
        # Cross-household access returns 404 (security: prevents probing)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    return _category_to_response(category)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    request: UpdateCategoryRequest,
    service: CategoryService = Depends(get_category_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CategoryResponse:
    """Update a category."""
    cat_id = CategoryId.from_string(category_id)
    user_id = current_user.user_id

    # Update name if provided
    if request.name is not None:
        result = await service.update_category_name(user_id, cat_id, request.name)
        if isinstance(result, CategoryError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": result.code, "message": result.message},
            )

    # Update parent if provided (including setting to None for top-level)
    if request.parent_id is not None or "parent_id" in request.model_fields_set:
        parent_id = (
            CategoryId.from_string(request.parent_id) if request.parent_id else None
        )
        result = await service.update_category_parent(user_id, cat_id, parent_id)
        if isinstance(result, CategoryError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": result.code, "message": result.message},
            )

    # Fetch updated category
    category = service.get_category(cat_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return _category_to_response(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    reassign_to: str | None = Query(
        default=None, description="Category to reassign transactions to"
    ),
    service: CategoryService = Depends(get_category_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """Delete a category."""
    cat_id = CategoryId.from_string(category_id)
    reassign_id = CategoryId.from_string(reassign_to) if reassign_to else None

    result = await service.delete_category(
        current_user.user_id,
        cat_id,
        reassign_id,
        household_id=current_user.household_id,
    )

    if isinstance(result, CategoryError):
        status_code = status.HTTP_400_BAD_REQUEST
        if result.code == "NOT_FOUND":
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail={"code": result.code, "message": result.message},
        )

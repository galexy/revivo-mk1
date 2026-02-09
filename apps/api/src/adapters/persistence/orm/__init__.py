"""SQLAlchemy ORM configuration and table definitions.

This package contains:
- base.py: Metadata and registry configuration
- tables.py: Table definitions (separate from domain models)
- mappers.py: Imperative mapping between domain and ORM
"""

from .base import mapper_registry, metadata

__all__ = ["metadata", "mapper_registry"]

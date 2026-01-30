"""SQLAlchemy base configuration.

Provides the shared metadata and mapper registry for the entire application.
Using imperative mapping keeps domain models pure (no SQLAlchemy imports).

The naming convention ensures consistent constraint names across all tables,
which is essential for:
- Readable migration scripts (Alembic uses these names)
- Debugging database errors (constraint names are meaningful)
- Cross-database compatibility
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import registry

# Naming convention for constraints (helps with migrations)
# See: https://docs.sqlalchemy.org/en/20/core/constraints.html#configuring-constraint-naming-conventions
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)

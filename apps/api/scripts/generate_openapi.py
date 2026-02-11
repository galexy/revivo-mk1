"""Generate OpenAPI JSON schema from FastAPI app.

Usage:
    uv run --package personal-finance-api python apps/api/scripts/generate_openapi.py > openapi.json
"""

import json
import sys

from src.adapters.api.app import create_app


def main() -> None:
    """Generate OpenAPI schema and write to stdout."""
    app = create_app()
    openapi_schema = app.openapi()
    json.dump(openapi_schema, sys.stdout, indent=2)


if __name__ == "__main__":
    main()

# Personal Finance Platform

A modern personal finance application that provides data sovereignty and proper domain modeling of real-world financial transactions. Built with Domain-Driven Design and Clean Architecture principles.

## Features

- Multiple account types: checking, savings, credit cards, loans, brokerage, retirement, rewards
- Transaction management with Plaid integration for bank sync
- Split transactions and complex transaction modeling (mortgage payments, ESPP, options)
- Envelope budgeting with smart suggestions
- Multiple interfaces: Web UI, REST API, CLI, AI integration

## Quick Start

### Using VS Code Devcontainer (Recommended)

1. Install [Docker](https://docs.docker.com/get-docker/) and [VS Code](https://code.visualstudio.com/)
2. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Clone this repository
4. Open in VS Code and click "Reopen in Container" when prompted
5. Wait for the container to build and dependencies to install

The devcontainer will automatically:
- Start PostgreSQL database
- Install Python dependencies via uv
- Configure VS Code with Python, Ruff, and Pylance extensions

### Manual Setup

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Start services
docker compose up -d

# Run database migrations
uv run alembic upgrade head

# Start the development server
uv run uvicorn src.adapters.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/domain/test_money.py
```

### Code Quality

```bash
# Run linter
uv run ruff check .

# Run formatter
uv run ruff format .

# Run type checker
uv run mypy src/

# Check architecture boundaries
uv run lint-imports
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run hooks manually on all files
uv run pre-commit run --all-files
```

## Architecture

This project follows **Hexagonal Architecture** (Ports and Adapters) with **Domain-Driven Design** principles:

```
src/
    domain/             # Pure domain logic (no infrastructure imports)
        model/          # Entities, Aggregates, Value Objects
        events/         # Domain events
        ports/          # Abstract interfaces (repositories, services)
        services/       # Domain services (cross-aggregate logic)
        exceptions.py   # Domain exceptions

    adapters/           # Infrastructure implementations
        persistence/    # Database adapters (SQLAlchemy)
        api/            # HTTP/REST adapters (FastAPI)
        security/       # Encryption, secrets

    application/        # Use cases / Application services
        services/       # Thin orchestration layer
```

### Key Patterns

- **Data Mapper**: Domain entities are persistence-ignorant (no ORM decorators)
- **Repository + Unit of Work**: Explicit transaction boundaries
- **Outbox Pattern**: Reliable domain event delivery
- **Result Type**: Expected failures use `Result` monad, exceptions for bugs
- **Prefixed IDs**: Stripe-style identifiers (e.g., `acct_xxx`, `txn_xxx`)

### Architecture Enforcement

Import-linter is configured to enforce boundaries:
- Domain layer cannot import infrastructure (SQLAlchemy, FastAPI, Pydantic)
- Adapters are independent of each other
- Dependencies flow inward following hexagonal architecture

## Documentation

- [Project Overview](.planning/PROJECT.md) - Requirements and constraints
- [Roadmap](.planning/ROADMAP.md) - Development phases
- [Phase Documentation](.planning/phases/) - Detailed phase plans and summaries

## License

MIT

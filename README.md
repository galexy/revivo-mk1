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

# Install Node.js (for Nx monorepo tooling)
# See https://nodejs.org/

# Install all workspace dependencies (Python + Node)
uv sync --all-packages
pnpm install

# Start services
docker compose up -d

# Run database migrations
cd apps/api && uv run --package personal-finance-api alembic upgrade head

# Start the development server
npx nx serve api
```

## Monorepo Structure

This project uses [Nx](https://nx.dev) to manage a polyglot monorepo with [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/) for Python packages and [pnpm](https://pnpm.io) for Node packages.

```
/
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   └── web/          # React frontend (TypeScript)
├── libs/
│   ├── domain/       # Shared domain layer (Python)
│   └── ui/           # Shared UI components (shadcn/ui)
├── nx.json           # Nx workspace config
└── pyproject.toml    # Root Python config (uv workspace)
```

### Nx Projects

```bash
npx nx show projects    # List all projects: api, domain, web, ui
npx nx graph            # Visualize project dependency graph
```

## Development

All tasks are run through Nx. Do not invoke the underlying tools (pytest, ruff, eslint, etc.) directly.

### Running Tests

```bash
# Run tests for a specific project
npx nx test api
npx nx test domain
npx nx test web

# Run tests across all projects
npx nx run-many -t test
```

### Code Quality

```bash
# Lint a specific project
npx nx lint api
npx nx lint domain
npx nx lint web

# Type check a specific project
npx nx typecheck api
npx nx typecheck domain
npx nx typecheck web

# Format check a specific project
npx nx format api
npx nx format domain
npx nx format web

# Run across all projects
npx nx run-many -t lint typecheck
npx nx run-many -t format
```

### Database Migrations

```bash
# Run migrations
cd apps/api && uv run --package personal-finance-api alembic upgrade head

# Generate a new migration after changing tables.py
cd apps/api && uv run --package personal-finance-api alembic revision --autogenerate -m "description"

# Check for schema drift
cd apps/api && uv run --package personal-finance-api alembic check
```

## Architecture

This project follows **Hexagonal Architecture** (Ports and Adapters) with **Domain-Driven Design** principles:

```
apps/api/src/
    adapters/           # Infrastructure implementations
        persistence/    # Database adapters (SQLAlchemy)
        api/            # HTTP/REST adapters (FastAPI)
        security/       # Encryption, secrets
    application/        # Use cases / Application services
        services/       # Thin orchestration layer

libs/domain/domain/
    model/              # Entities, Aggregates, Value Objects
    events/             # Domain events
    ports/              # Abstract interfaces (repositories, services)
    services/           # Domain services (cross-aggregate logic)
    exceptions.py       # Domain exceptions
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

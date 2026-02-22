# Personal Finance Platform

A modern personal finance application that provides data sovereignty and proper domain modeling of real-world financial transactions. Built with Domain-Driven Design and Clean Architecture principles.

## Features

- Multiple account types: checking, savings, credit cards, loans, brokerage, retirement, rewards
- Transaction management with Plaid integration for bank sync
- Split transactions and complex transaction modeling (mortgage payments, ESPP, options)
- Envelope budgeting with smart suggestions
- Multiple interfaces: Web UI, REST API, CLI, AI integration

## Quick Start

### Using Claude Code Web

Claude Code Web environments come with PostgreSQL 16 pre-installed. A SessionStart hook automatically configures the database on session start.

If you need to set up manually:

```bash
sudo bash scripts/setup-postgres.sh
uv sync --all-packages
pnpm install
cd apps/api && uv run --package personal-finance-api alembic upgrade head
npx nx serve api
```

No Docker is needed — all code defaults to `localhost:5432` when no environment variables are set.

### Using VS Code Devcontainer

1. Install [Docker](https://docs.docker.com/get-docker/) and [VS Code](https://code.visualstudio.com/)
2. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Clone this repository
4. Open in VS Code and click "Reopen in Container" when prompted
5. Wait for the container to build and dependencies to install

The devcontainer will automatically:
- Start PostgreSQL database
- Install Python dependencies via uv
- Configure VS Code with Python, Ruff, and Pylance extensions

### Manual Setup (without Docker)

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Node.js (for Nx monorepo tooling)
# See https://nodejs.org/

# Install all workspace dependencies (Python + Node)
uv sync --all-packages
pnpm install

# Set up PostgreSQL (requires local PostgreSQL 16 installation)
sudo bash scripts/setup-postgres.sh

# Run database migrations
cd apps/api && uv run --package personal-finance-api alembic upgrade head

# Start the development server
npx nx serve api
```

### Manual Setup (with Docker)

```bash
uv sync --all-packages
pnpm install
docker compose up -d
cd apps/api && uv run --package personal-finance-api alembic upgrade head
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

## Making Changes with GSD (Claude Code)

This project uses the [GSD workflow](https://github.com/coleam00/gsd) with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) for AI-assisted development. Work is organized into **phases** (a coherent feature or capability) broken down into **plans** (atomic units of work). All planning artifacts live in `.planning/`.

### Workflow Overview

1. **Check progress** — See where the project stands and what's next
2. **Plan a phase** — Research the approach, create detailed execution plans
3. **Execute a phase** — Run all plans with parallel agents, atomic commits, and verification
4. **Verify the work** — Validate features through acceptance testing

### Common Commands

Run these as slash commands inside Claude Code:

| Command | Purpose |
|---|---|
| `/gsd:progress` | Check project status, see current phase, and route to next action |
| `/gsd:discuss-phase` | Flesh out the details and refine the requirements for a phase with the help of Claude  |
| `/gsd:plan-phase` | Research and create detailed plans for the next phase |
| `/gsd:execute-phase` | Execute all plans in a phase (parallel agents, atomic commits) |
| `/gsd:verify-work` | Run conversational UAT to validate built features |
| `/gsd:quick` | Execute a small task with GSD guarantees (atomic commits, state tracking) |
| `/gsd:debug` | Systematic debugging with persistent state across context resets |

### Planning and Roadmap Commands

| Command | Purpose |
|---|---|
| `/gsd:new-milestone` | Start a new milestone cycle |
| `/gsd:add-phase` | Add a phase to the end of the current milestone |
| `/gsd:insert-phase` | Insert urgent work as a decimal phase (e.g., 12.1) between existing phases |
| `/gsd:remove-phase` | Remove a future phase and renumber subsequent phases |
| `/gsd:discuss-phase` | Gather context through adaptive questioning before planning |
| `/gsd:list-phase-assumptions` | Surface Claude's assumptions about a phase before planning |

### Session Management

| Command | Purpose |
|---|---|
| `/gsd:pause-work` | Create context handoff when pausing work mid-phase |
| `/gsd:resume-work` | Resume work from a previous session with full context restoration |
| `/gsd:add-todo` | Capture an idea or task as a todo for later |
| `/gsd:check-todos` | List pending todos and pick one to work on |

### Milestone Lifecycle

| Command | Purpose |
|---|---|
| `/gsd:audit-milestone` | Audit milestone completion against original intent |
| `/gsd:plan-milestone-gaps` | Create phases to close gaps identified by the audit |
| `/gsd:complete-milestone` | Archive a completed milestone and prepare for the next one |

### Typical Workflow Example

```
# 1. Check where we are
/gsd:progress

# 2. Discuss the next phase
/gsd:discuss-phase <phase>

# 3. Plan the next phase (researches approach, creates PLAN.md files)
/gsd:plan-phase <phase>
-- READ EACH PLAN file and give feedback

# 3. Execute the phase (spawns parallel agents per plan)
/gsd:execute-phase <phase>
-- READ EACH SUMMARY file and look for where agent took shortcuts

# 5. Verify the work (conversational acceptance testing)
/gsd:verify-work <phase>
```

### Planning Artifacts

All GSD state is tracked in `.planning/`:

```
.planning/
├── PROJECT.md          # Project requirements and constraints
├── REQUIREMENTS.md     # Detailed requirements
├── ROADMAP.md          # All phases with status
├── STATE.md            # Current position, velocity metrics
├── CHECKPOINTS.md      # Validation rules for development
└── phases/
    └── XX-phase-name/
        ├── XX-NN-PLAN.md     # Execution plan for each unit of work
        ├── XX-NN-SUMMARY.md  # What was done after execution
        └── VERIFICATION.md   # Phase verification results
```

## Documentation

- [Project Overview](.planning/PROJECT.md) - Requirements and constraints
- [Roadmap](.planning/ROADMAP.md) - Development phases
- [Phase Documentation](.planning/phases/) - Detailed phase plans and summaries

## License

MIT

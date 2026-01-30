# Stack Research: Personal Finance Application

**Domain:** Personal Finance / Fintech
**Researched:** 2026-01-29
**Confidence:** HIGH (core stack pre-selected, supporting libraries verified via official sources)

## Executive Summary

This research validates and extends the pre-selected technology stack for a modern personal finance platform. The core choices (Python/FastAPI/PostgreSQL/SQLAlchemy backend, React/TypeScript frontend) are well-suited for DDD + Clean Architecture. This document identifies the supporting libraries, patterns, and integrations needed to complete the stack.

**Key Findings:**
- Zustand + TanStack Query is the recommended state management approach for React (replaces Redux for most use cases)
- Plaid Python SDK (v7.2.1+) is mature and well-maintained for bank integrations
- SQLAlchemy 2.0's imperative mapping supports DDD patterns, though the maintainers note it's not strictly necessary
- OpenTelemetry has first-class FastAPI instrumentation
- @hey-api/openapi-ts generates type-safe clients from FastAPI's OpenAPI spec

---

## Recommended Stack

### Core Backend (Pre-Selected)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | 3.12+ | Runtime | LTS, full async support, FastAPI compatible. 3.13/3.14 also supported. | HIGH |
| FastAPI | 0.115+ | Web Framework | Async-native, automatic OpenAPI, Pydantic integration, excellent DI via `Depends`. Best-in-class for DDD with Clean Architecture. | HIGH |
| Pydantic | 2.12.5 | Validation/Serialization | Type-safe validation, settings management, 6.5x faster than v1. Required for FastAPI. | HIGH |
| PostgreSQL | 16+ | Database | ACID compliance critical for financial data. JSON support for flexible schemas. | HIGH |
| SQLAlchemy | 2.0.46 | ORM | Data mapper pattern support, Unit of Work built-in. Async support via `asyncpg`. | HIGH |
| Alembic | 1.18.3 | Migrations | First-party SQLAlchemy support, autogenerate, batch operations. | HIGH |

### Core Frontend (Pre-Selected)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| React | 18.3+ / 19 | UI Framework | Component model, hooks, concurrent features. React 19 adds Server Components. | HIGH |
| TypeScript | 5.5+ | Type Safety | Required for Zod integration, IDE support, type inference. Strict mode required. | HIGH |
| Vite | 6.0+ | Build Tool | Fast HMR, native ESM, excellent TypeScript support. Required for Vitest. | HIGH |

### State Management (Frontend)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Zustand | 5.0.10 | Client State | 1KB bundle, no boilerplate, hooks-based. Perfect for UI state (modals, filters, preferences). Simpler than Redux, more structured than Context. | HIGH |
| TanStack Query | 5.90.19 | Server State | Caching, background refetch, optimistic updates. Handles ~80% of state in data-heavy apps. Reduces Redux usage to ~10% of new projects. | HIGH |

**Architecture Rationale:** Zustand handles client-only state (UI preferences, filters, form drafts). TanStack Query handles all server-synchronized state (accounts, transactions, budgets). This separation eliminates the need for Redux in most cases.

**Do NOT use Redux Toolkit** unless you have enterprise requirements (multiple large teams, complex client-side business logic). For a personal finance app, Zustand + TanStack Query is simpler and sufficient.

### Forms & Validation (Frontend)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| React Hook Form | 7.71.1 | Form State | Minimal re-renders, uncontrolled inputs, excellent TypeScript support. 8.x in beta. | HIGH |
| Zod | 4.3.5 | Schema Validation | TypeScript-first, 14x faster than v3 for strings. Generates types from schemas. Share schemas with backend via OpenAPI. | HIGH |
| @hookform/resolvers | 4.x | Integration | Bridges React Hook Form + Zod. Use `zodResolver`. | HIGH |

**Pattern:** Define Zod schemas, infer TypeScript types with `z.infer<typeof schema>`, use `zodResolver` with React Hook Form. Same schemas can validate on client and server.

### API Client Generation

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| @hey-api/openapi-ts | 0.89.2 | TypeScript Client Gen | Generates SDKs, Zod schemas, TanStack Query hooks from OpenAPI spec. Used by Vercel, PayPal. | HIGH |

**Pattern:** FastAPI auto-generates OpenAPI spec. Run `npx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o src/client` to generate type-safe client. Regenerate on API changes.

**Alternative considered:** `openapi-typescript-codegen` - deprecated, maintainers recommend @hey-api/openapi-ts.

### Financial Domain Libraries

| Library | Version | Purpose | Why Recommended | Confidence |
|---------|---------|---------|-----------------|------------|
| plaid-python | 29.x (latest) | Bank Integration | Official Plaid SDK, monthly updates, async support. Well-documented with sandbox. | HIGH |
| python-money (py-money) | 0.4.x | Money Types | Vimeo's library. Auto-rounds to currency precision, prevents invalid currency ops. | MEDIUM |
| decimal (stdlib) | N/A | Precision Math | Built-in, required for financial calculations. Never use `float` for money. | HIGH |

**Money Handling Pattern:**
```python
from decimal import Decimal, ROUND_HALF_UP
from money import Money

# Always use Decimal for storage/calculations
amount = Decimal("123.45")
# Use Money for display/currency-aware operations
price = Money("19.99", "USD")
```

**Plaid Integration Pattern:**
- Store `client_id` and `secret` in environment variables, never in code
- Store `access_token` encrypted in database
- Use webhooks for transaction updates (INITIAL_UPDATE, HISTORICAL_UPDATE)
- Test thoroughly in Sandbox before Production

### Dependency Injection & DDD Support

| Library | Version | Purpose | Why Recommended | Confidence |
|---------|---------|---------|-----------------|------------|
| dependency-injector | 4.48.3 | DI Container | Written in Cython for performance. Factory, Singleton, Resource providers. FastAPI integration. | MEDIUM |
| FastAPI Depends | Built-in | Request-scoped DI | Native to FastAPI. Use for request-scoped dependencies (db sessions, current user). | HIGH |

**DDD Architecture Pattern:**
```
src/
  domain/           # Pure Python, no framework imports
    entities/       # Account, Transaction, Budget (business logic)
    value_objects/  # Money, AccountNumber, CategoryId
    repositories/   # Abstract interfaces (ABC)
    services/       # Domain services
  application/      # Use cases, DTOs, orchestration
    use_cases/      # One class per use case, single execute() method
  infrastructure/   # Framework-specific implementations
    persistence/    # SQLAlchemy repositories
    api/            # FastAPI routers (thin controllers)
    plaid/          # Plaid adapter
```

**Use FastAPI Depends for:**
- Database sessions (request-scoped)
- Current authenticated user
- Repositories (injected into use cases)

**Use dependency-injector for:**
- Application-wide singletons (config, Plaid client)
- Complex dependency graphs across layers

### Observability Stack (Pre-Selected + Extensions)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| opentelemetry-instrumentation-fastapi | 0.50+ | Auto-instrumentation | Official OTel package. Automatic tracing for all HTTP requests. | HIGH |
| opentelemetry-sdk | 1.29+ | OTel Core | Required base for traces, metrics, logs. | HIGH |
| opentelemetry-exporter-otlp | 1.29+ | Export to Grafana | OTLP protocol for Grafana Tempo/Loki/Mimir. | HIGH |
| opentelemetry-instrumentation-sqlalchemy | 0.50+ | DB Tracing | Automatic SQL query tracing. Shows slow queries in traces. | HIGH |
| opentelemetry-instrumentation-httpx | 0.50+ | HTTP Client Tracing | Traces outbound HTTP calls (Plaid API). | HIGH |

**OTel Setup Pattern:**
```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
```

### Background Tasks

| Technology | Version | Purpose | When to Use | Confidence |
|------------|---------|---------|-------------|------------|
| FastAPI BackgroundTasks | Built-in | Simple async tasks | Fire-and-forget: emails, logs, notifications. No persistence. | HIGH |
| ARQ | 0.26+ | Async Redis Queue | I/O-bound tasks needing reliability: Plaid sync, report generation. Native asyncio. | MEDIUM |
| Celery | 5.4+ | Enterprise Queue | CPU-intensive tasks, complex workflows, multi-server. Overkill for personal finance app. | LOW (not recommended) |

**Recommendation:** Start with FastAPI BackgroundTasks. Add ARQ + Redis when you need:
- Task persistence (survive restarts)
- Retries with backoff
- Scheduled jobs (daily balance sync)
- Status tracking

**Avoid Celery** unless you have proven need for its complexity.

### Testing Stack

#### Backend Testing

| Library | Version | Purpose | Why Recommended | Confidence |
|---------|---------|---------|-----------------|------------|
| pytest | 9.0.2 | Test Framework | Standard for Python. Fixtures, parametrize, plugins. | HIGH |
| pytest-asyncio | 1.3.0 | Async Testing | Required for testing async FastAPI endpoints. | HIGH |
| pytest-cov | 6.0+ | Coverage | Integrates coverage.py with pytest. | HIGH |
| httpx | 0.28.1 | Test Client | AsyncClient for testing FastAPI. Same API as requests. | HIGH |
| factory-boy | 3.3+ | Test Fixtures | Model factories for realistic test data. | MEDIUM |
| respx | 0.22+ | HTTP Mocking | Mock httpx requests (for Plaid API in tests). | MEDIUM |

**Testing Pattern:**
```python
# tests/conftest.py
@pytest.fixture
async def client(test_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def test_db():
    # Use separate test database
    # Override get_db dependency
```

#### Frontend Testing

| Library | Version | Purpose | Why Recommended | Confidence |
|---------|---------|---------|-----------------|------------|
| Vitest | 4.0.17 | Test Framework | 10-20x faster than Jest on large codebases. Native Vite integration. | HIGH |
| @testing-library/react | 16.x | Component Testing | Tests behavior, not implementation. Accessibility-first queries. | HIGH |
| @testing-library/user-event | 14.x | User Interactions | Simulates real user events (click, type, etc.). | HIGH |
| msw | 2.x | API Mocking | Service Worker-based mocking. Works in tests and dev. | HIGH |

**Testing Pyramid:**
- Unit tests: Domain logic, pure functions (many, fast)
- Integration tests: API contracts, DB queries (some)
- E2E tests: Critical flows only - login, transaction entry, reconciliation (few, 5-15 max)

---

## Configuration & Settings

| Library | Version | Purpose | Why Recommended | Confidence |
|---------|---------|---------|-----------------|------------|
| pydantic-settings | 2.12.0 | Config Management | Loads from env vars, .env files, secrets. Type-safe. | HIGH |

**Settings Pattern:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__"
    )

    database_url: str
    plaid_client_id: str
    plaid_secret: str  # SecretStr for sensitive values
    plaid_environment: str = "sandbox"
```

---

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| State Management | Zustand + TanStack Query | Redux Toolkit | Large teams (10+), complex client-side business logic, need for Redux DevTools |
| State Management | Zustand | Jotai | Fine-grained atomic state, complex interdependencies, heavy Suspense usage |
| ORM | SQLAlchemy | SQLModel | Simpler projects where domain model = data model is acceptable. Loses DDD separation. |
| Background Tasks | ARQ | Celery | CPU-intensive tasks, multi-server, need RabbitMQ/SQS broker |
| Form Library | React Hook Form | Formik | Existing Formik codebase. RHF is faster and has better TS support. |
| Test Framework (FE) | Vitest | Jest | Legacy Jest setup, React Native, need mature ecosystem |
| Money Library | py-money | stockholm | Need GraphQL/Protobuf serialization, currency exchange rates |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `float` for money | Binary floating-point causes rounding errors | `Decimal` or money library |
| Redux for simple state | Overkill, excessive boilerplate | Zustand + TanStack Query |
| SQLModel for DDD | Couples domain to persistence | SQLAlchemy with imperative/classical mapping |
| Celery for I/O tasks | Overcomplicated for async tasks | ARQ or FastAPI BackgroundTasks |
| openapi-typescript-codegen | Deprecated, unmaintained | @hey-api/openapi-ts |
| Jest for new Vite projects | Slower, requires configuration | Vitest (native Vite support) |
| Pydantic v1 | Deprecated, no Python 3.14 support | Pydantic v2.12+ |
| unittest for new code | Verbose, limited fixtures | pytest |

---

## DDD + Clean Architecture Alignment

### How Stack Supports DDD

| Principle | Stack Support |
|-----------|---------------|
| **Domain Independence** | SQLAlchemy imperative mapping keeps domain entities framework-free. FastAPI stays in infrastructure layer only. |
| **Dependency Inversion** | FastAPI Depends + dependency-injector enable constructor injection. Repositories are abstract interfaces. |
| **Value Objects** | Pydantic models work well as value objects with validation. Can also use plain dataclasses. |
| **Repository Pattern** | SQLAlchemy Session enables Unit of Work. Map imperatively to keep domain clean. |
| **Use Cases** | One class per use case with single `execute()` method. Inject repositories via DI. |
| **DTOs** | Pydantic models for API request/response. Keep separate from domain entities. |

### SQLAlchemy Mapping Strategy

**Option 1: Imperative Mapping (Recommended for strict DDD)**
```python
# domain/entities/account.py - Pure Python
@dataclass
class Account:
    id: UUID
    name: str
    balance: Decimal

    def deposit(self, amount: Decimal) -> None:
        self.balance += amount

# infrastructure/persistence/mappings.py
from sqlalchemy.orm import registry
mapper_registry = registry()

account_table = Table("accounts", mapper_registry.metadata, ...)
mapper_registry.map_imperatively(Account, account_table)
```

**Option 2: Declarative with Separation (Pragmatic approach)**
```python
# infrastructure/persistence/models.py
class AccountModel(Base):
    __tablename__ = "accounts"
    # SQLAlchemy columns

    def to_entity(self) -> Account:
        return Account(...)

    @classmethod
    def from_entity(cls, entity: Account) -> "AccountModel":
        return cls(...)
```

**Note:** SQLAlchemy maintainers state imperative mapping "is not recommended overall" because mappings modify class behavior anyway. The pragmatic approach (Option 2) with explicit mappers is often cleaner.

---

## Version Compatibility Matrix

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| FastAPI 0.115+ | Pydantic 2.12+ | Pydantic v1 support deprecated |
| FastAPI 0.115+ | Starlette 0.40-0.45 | Check release notes for exact version |
| SQLAlchemy 2.0.46 | Alembic 1.18+ | Use matching major versions |
| SQLAlchemy 2.0.46 | Python 3.10-3.14 | Wheels for all platforms |
| Pydantic 2.12 | Python 3.9+ | Python 3.8 dropped |
| pytest 9.0 | Python 3.10+ | Python 3.9 dropped |
| Vitest 4.0 | Vite 6.0+ | Use matching major versions |
| TanStack Query 5.x | React 18+ | Also supports React 19 |
| Zustand 5.x | React 18+ | Supports React 19 |

---

## Installation Commands

### Backend

```bash
# Core
pip install fastapi[standard] uvicorn[standard]
pip install sqlalchemy[asyncio] asyncpg alembic
pip install pydantic pydantic-settings

# Financial
pip install plaid-python py-money

# Observability
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-otlp
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-sqlalchemy
pip install opentelemetry-instrumentation-httpx

# Background Tasks (when needed)
pip install arq

# DI (optional, can use FastAPI Depends only)
pip install dependency-injector

# Testing
pip install pytest pytest-asyncio pytest-cov
pip install httpx respx factory-boy
```

### Frontend

```bash
# Core
npm install react react-dom
npm install -D typescript @types/react @types/react-dom

# State Management
npm install zustand @tanstack/react-query

# Forms
npm install react-hook-form zod @hookform/resolvers

# API Client Generation
npm install -D @hey-api/openapi-ts

# Testing
npm install -D vitest @vitest/ui jsdom
npm install -D @testing-library/react @testing-library/user-event @testing-library/jest-dom
npm install -D msw
```

---

## Sources

### HIGH Confidence (Official Documentation)
- [FastAPI Official Docs](https://fastapi.tiangolo.com/) - Testing, dependencies, async
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/) - ORM patterns, mapping
- [Pydantic Settings Docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [OpenTelemetry FastAPI Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [Plaid API Documentation](https://plaid.com/docs/api/)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Zustand Documentation](https://zustand.docs.pmnd.rs/)
- [Vitest Documentation](https://vitest.dev/)
- [React Hook Form Docs](https://react-hook-form.com/)
- [Zod Documentation](https://zod.dev/)

### MEDIUM Confidence (GitHub, Verified Community Sources)
- [Plaid Python GitHub](https://github.com/plaid/plaid-python)
- [SQLAlchemy DDD Discussion](https://github.com/sqlalchemy/sqlalchemy/discussions/9180) - Imperative mapping perspective
- [fastapi-clean-example](https://github.com/ivan-borovets/fastapi-clean-example) - DDD + Clean Architecture patterns
- [python-clean-architecture](https://github.com/alefeans/python-clean-architecture) - Production template
- [Hey API GitHub](https://github.com/hey-api/openapi-ts)
- [Cosmic Python - Repository Pattern](https://www.cosmicpython.com/book/chapter_02_repository.html)

### Version Information (PyPI/npm, January 2026)
- FastAPI: 0.115+ (Python 3.9+, Pydantic 2.12+)
- SQLAlchemy: 2.0.46 (January 21, 2026)
- Alembic: 1.18.3 (January 29, 2026)
- Pydantic: 2.12.5
- pytest: 9.0.2 (December 2025)
- pytest-asyncio: 1.3.0
- httpx: 0.28.1
- Zustand: 5.0.10
- TanStack Query: 5.90.19
- Vitest: 4.0.17
- React Hook Form: 7.71.1
- Zod: 4.3.5
- @hey-api/openapi-ts: 0.89.2

---

*Stack research for: Personal Finance Application*
*Researched: 2026-01-29*
*Confidence: HIGH*

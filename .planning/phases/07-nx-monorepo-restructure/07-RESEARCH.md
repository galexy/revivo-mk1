# Phase 7: Nx Monorepo Restructure - Research

**Researched:** 2026-02-07
**Domain:** Nx monorepo tooling, Python project restructuring, uv workspaces
**Confidence:** MEDIUM

## Summary

This phase converts a single-app Python project into an Nx monorepo with `apps/api` (FastAPI backend), `apps/web` (empty frontend scaffold), `libs/domain` (extracted domain layer), and `libs/ui` (empty future shadcn/ui scaffold). The project currently uses `uv` for Python dependency management, has 444 tests across unit and integration suites, and all code lives under `src/` with `src.domain.*`, `src.application.*`, and `src.adapters.*` import paths.

The recommended approach is: (1) initialize Nx at repo root with `nx init`, (2) use `nx:run-commands` executor for Python targets rather than `@nxlv/python` plugin to avoid complexity, (3) leverage uv workspaces for Python dependency management across apps/libs, (4) move files with `git mv` for history preservation, and (5) update all import paths from `src.domain.*` to `domain.*` for the extracted domain library.

**Primary recommendation:** Use Nx as the task runner with `nx:run-commands` for Python projects, combined with uv workspaces (`tool.uv.workspace`) for Python dependency management. Do NOT use `@nxlv/python` plugin -- it adds complexity (Poetry/uv abstraction layer, root pyproject.toml conflicts) that is unnecessary for this project.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Directory Layout
- Backend app at `apps/api/` (not "backend")
- Frontend app at `apps/web/` (not "frontend")
- Domain layer extracted to `libs/domain/` as shared library
- Future shadcn/ui components will live at `libs/ui/` (see https://ui.shadcn.com/docs/monorepo)
- Flat libs structure: `libs/domain`, `libs/ui` (no language namespace)
- Tests colocated with projects: `apps/api/tests/`, `libs/domain/tests/`
- Docker files (Dockerfile, docker-compose.yml) stay at repo root
- `.planning/` directory stays at repo root (project-wide, not app-specific)

#### Migration Strategy
- Incremental commits (not big-bang) -- init Nx, move backend, extract domain, scaffold frontend
- Preserve git history using `git mv` for moved files
- Rename import paths to match new structure (e.g., `from domain.model import ...` not `from app.domain.model import ...`)
- Validation checkpoint: all tests pass + UAT tests rerun + Nx commands work

#### Build & Dev Workflow
- Python dependency management: Claude's discretion based on Nx Python plugin conventions
- Devcontainer: fix what breaks only (Docker context paths, volume mounts, working directories). No new features.
- CLAUDE.md updated this phase to document monorepo structure, import conventions, Nx commands, directory layout for future shadcn/ui
- Nx task definitions (build, test, lint) set up for both apps/api and apps/web

#### Frontend Scaffold
- `apps/web/` is empty directory + `project.json` only (no React code -- Phase 8)
- Minimal `package.json` at `apps/web/` (name + version, no deps)
- `libs/ui/` scaffolded as empty Nx project + `project.json` (ready for Phase 8 shadcn/ui setup)
- `libs/domain/` gets `project.json` with test/lint targets

### Claude's Discretion
- Alembic migrations location (likely `apps/api/alembic/` since API owns the database)
- Python dependency management approach (per-project vs root pyproject.toml)
- Exact Nx plugin choices for Python projects
- Nx workspace configuration details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Nx | 21.x (latest) | Monorepo task runner, dependency graph, caching | Industry standard monorepo tool, polyglot support, works without language-specific plugins |
| uv | (already installed) | Python dependency management + workspace support | Already used by project; native workspace support via `tool.uv.workspace` in pyproject.toml |
| Node.js | 20.x (already installed) | Nx runtime + future frontend tooling | Already in devcontainer, required by Nx |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| nx:run-commands | built-in | Execute arbitrary shell commands as Nx targets | All Python targets (test, lint, build) -- avoids plugin dependency |
| git mv | built-in | Move files preserving history | All file moves during restructure |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| nx:run-commands | @nxlv/python plugin (v21.2.0) | Plugin adds Poetry/uv abstraction, project generators, dependency bundling. But: it creates root pyproject.toml that can break non-Python apps, adds configuration complexity, and this project only needs simple test/lint/serve commands. **Recommendation: skip the plugin.** |
| uv workspaces | Per-project independent venvs | Independent venvs waste disk space and are harder to manage. uv workspaces provide a shared lockfile with per-project pyproject.toml, which aligns perfectly with the monorepo structure. **Recommendation: use uv workspaces.** |
| Nx | Turborepo | Nx has better polyglot support, task graph visualization, and plugin ecosystem. Project is already using npm. **Recommendation: stay with Nx per user decision.** |

**Installation:**
```bash
# Initialize Nx in existing repo
npx nx@latest init

# This creates nx.json at repo root
# No additional npm packages needed for Python targets
```

## Architecture Patterns

### Recommended Project Structure
```
/                                # Workspace root
├── nx.json                      # Nx workspace configuration
├── package.json                 # Root package.json (Nx + mjml deps)
├── pyproject.toml               # Root Python project + uv workspace config
├── uv.lock                      # Shared lockfile for all Python packages
├── alembic.ini                  # Alembic config (points to apps/api/alembic/)
├── docker-compose.yml           # Docker Compose (stays at root)
├── docker-compose.override.yml  # Dev overrides (stays at root)
├── .devcontainer/               # Devcontainer config (stays at root)
├── .planning/                   # Planning docs (stays at root)
├── CLAUDE.md                    # Project instructions (updated)
├── Makefile                     # Root Makefile (updated paths)
├── .pre-commit-config.yaml      # Pre-commit hooks (updated paths)
│
├── apps/
│   ├── api/                     # FastAPI backend app
│   │   ├── project.json         # Nx project config (test, lint, serve targets)
│   │   ├── pyproject.toml       # Python package config for api
│   │   ├── src/                  # Backend source code
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── adapters/        # API routes, persistence, security, email, jobs
│   │   │   └── application/     # Services, event bus, handlers
│   │   ├── alembic/             # Alembic migrations directory
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   └── tests/               # API-specific tests (integration + unit for adapters/application)
│   │       ├── conftest.py
│   │       ├── integration/
│   │       └── unit/
│   │
│   └── web/                     # Frontend app scaffold (Phase 8)
│       ├── project.json         # Nx project config (empty targets)
│       └── package.json         # Minimal {name, version}
│
├── libs/
│   ├── domain/                  # Extracted domain layer
│   │   ├── project.json         # Nx project config (test, lint targets)
│   │   ├── pyproject.toml       # Python package config for domain lib
│   │   ├── domain/              # Domain source code (importable as `domain.*`)
│   │   │   ├── __init__.py
│   │   │   ├── exceptions.py
│   │   │   ├── model/
│   │   │   ├── events/
│   │   │   └── ports/
│   │   └── tests/               # Domain unit tests
│   │       ├── conftest.py
│   │       └── unit/
│   │
│   └── ui/                      # Future shadcn/ui components (Phase 8)
│       ├── project.json         # Nx project config (empty targets)
│       └── package.json         # Minimal {name, version}
│
├── scripts/                     # Utility scripts (stays at root)
├── secrets/                     # Secrets (stays at root)
└── docs/                        # Documentation (stays at root)
```

### Pattern 1: Nx Project Configuration with run-commands

**What:** Define test, lint, and serve targets using `nx:run-commands` for Python projects
**When to use:** All Python projects (apps/api, libs/domain)
**Example:**

```json
// apps/api/project.json
{
  "name": "api",
  "projectType": "application",
  "sourceRoot": "apps/api/src",
  "targets": {
    "serve": {
      "executor": "nx:run-commands",
      "options": {
        "command": "uvicorn src.adapters.api.app:app --host 0.0.0.0 --port 8000 --reload",
        "cwd": "apps/api"
      }
    },
    "test": {
      "executor": "nx:run-commands",
      "options": {
        "command": "python -m pytest tests/ -v --tb=short",
        "cwd": "apps/api"
      },
      "inputs": ["{projectRoot}/**/*.py", "libs/domain/**/*.py"],
      "outputs": []
    },
    "lint": {
      "executor": "nx:run-commands",
      "options": {
        "command": "ruff check src/ tests/",
        "cwd": "apps/api"
      },
      "inputs": ["{projectRoot}/**/*.py"],
      "outputs": []
    }
  }
}
```

```json
// libs/domain/project.json
{
  "name": "domain",
  "projectType": "library",
  "sourceRoot": "libs/domain/domain",
  "targets": {
    "test": {
      "executor": "nx:run-commands",
      "options": {
        "command": "python -m pytest tests/ -v --tb=short",
        "cwd": "libs/domain"
      },
      "inputs": ["{projectRoot}/**/*.py"],
      "outputs": []
    },
    "lint": {
      "executor": "nx:run-commands",
      "options": {
        "command": "ruff check domain/ tests/",
        "cwd": "libs/domain"
      },
      "inputs": ["{projectRoot}/**/*.py"],
      "outputs": []
    }
  }
}
```

### Pattern 2: uv Workspace Configuration

**What:** Configure uv workspaces for shared dependency management across Python packages
**When to use:** Root pyproject.toml to declare workspace members
**Example:**

```toml
# Root pyproject.toml
[project]
name = "personal-finance-workspace"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["apps/api", "libs/domain"]

[tool.uv]
dev-dependencies = [
    # Shared dev dependencies (testing, linting, formatting)
    "ruff>=0.8.0",
    "mypy>=1.14.0",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pre-commit>=4.0.0",
    "httpx>=0.28.0",
    "hypothesis>=6.121.0",
    "pyright>=1.1.0",
    "import-linter>=2.1.0",
]
```

```toml
# apps/api/pyproject.toml
[project]
name = "personal-finance-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "domain",  # workspace dependency
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    # ... all current runtime dependencies except domain-only ones
]

[tool.uv.sources]
domain = { workspace = true }
```

```toml
# libs/domain/pyproject.toml
[project]
name = "domain"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "typeid-python>=0.3.0",
    "returns>=0.23.0",
    # Only dependencies used by the domain layer
]
```

### Pattern 3: Import Path Convention After Restructure

**What:** All imports of the extracted domain layer use `domain.*` instead of `src.domain.*`
**When to use:** Every file that imports from the domain layer

```python
# BEFORE (current)
from src.domain.model.account import Account
from src.domain.model.entity_id import AccountId
from src.domain.events.base import DomainEvent

# AFTER (new)
from domain.model.account import Account
from domain.model.entity_id import AccountId
from domain.events.base import DomainEvent
```

For API-internal imports:
```python
# BEFORE (current)
from src.adapters.api.app import create_app
from src.application.services.account_service import AccountService

# AFTER (new)
from src.adapters.api.app import create_app
from src.application.services.account_service import AccountService
# API-internal imports keep `src.*` prefix since apps/api/src/ is the package root
```

### Pattern 4: Alembic Configuration in Monorepo

**What:** Move alembic directory to `apps/api/alembic/` and update configuration
**When to use:** Migration management after restructure

```ini
# alembic.ini (stays at repo root for convenience)
[alembic]
script_location = apps/api/alembic
prepend_sys_path = .
```

```python
# apps/api/alembic/env.py
# Update imports to use new paths
from src.adapters.persistence.orm.base import metadata  # relative to apps/api
import src.adapters.persistence.orm.tables  # noqa: F401
```

### Anti-Patterns to Avoid

- **Big-bang migration:** Moving everything in one commit loses git blame context. Do incremental commits: init Nx, move backend, extract domain, scaffold frontend.
- **Keeping `src.domain.*` imports:** After extraction, domain code should be importable as `domain.*`, not `src.domain.*`. The old import path creates a false dependency on the `src` package.
- **Using @nxlv/python for simple projects:** The plugin is designed for complex Python monorepos with dependency bundling needs. For this project, `nx:run-commands` is simpler and sufficient.
- **Duplicating dependencies:** Don't copy the same dependency into both `apps/api/pyproject.toml` and `libs/domain/pyproject.toml`. Domain dependencies belong in `libs/domain/pyproject.toml`; the API declares `domain` as a workspace dependency.
- **Moving Docker files into apps/:** Docker files must stay at repo root because the Docker build context is the repo root. Moving them would break the build.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Task orchestration | Custom Makefile targets for each project | Nx targets in project.json | Nx provides caching, dependency graph, affected commands |
| Python workspace deps | Manual sys.path manipulation | uv workspaces with `{ workspace = true }` | uv handles editable installs, lockfile resolution, and cross-package imports |
| File moving with history | cp + rm + git add | `git mv` | git mv preserves rename detection for blame/log --follow |
| Import path updates | Manual find-and-replace | Scripted sed/python replacements + verification | 180+ import statements need updating; manual editing is error-prone |

**Key insight:** The heaviest lift in this phase is the import path rewriting (~180 `from src.domain.*` imports across ~60 files). This must be automated, not manual. Use a script or systematic find-replace with verification.

## Common Pitfalls

### Pitfall 1: Python sys.path / PYTHONPATH Not Configured for Monorepo
**What goes wrong:** After moving files, `import domain.model.account` fails because Python can't find the `domain` package.
**Why it happens:** Python resolves imports via sys.path, which doesn't automatically include `libs/domain/` in the monorepo layout.
**How to avoid:** Use uv workspaces. When you run `uv sync`, workspace members are installed as editable packages, so `domain` becomes importable from anywhere in the workspace. Ensure `uv sync` is run after restructuring.
**Warning signs:** `ModuleNotFoundError: No module named 'domain'` during imports.

### Pitfall 2: Alembic Can't Find Metadata After Move
**What goes wrong:** `alembic upgrade head` or `alembic revision --autogenerate` fails with import errors.
**Why it happens:** Alembic's `env.py` imports `src.adapters.persistence.orm.base` and `src.adapters.persistence.orm.tables`. After moving to `apps/api/`, the Python path needs updating.
**How to avoid:** Keep `alembic.ini` at repo root with `script_location = apps/api/alembic` and `prepend_sys_path = apps/api`. Alternatively, run alembic from the `apps/api/` directory. Test migration commands after restructure.
**Warning signs:** `ModuleNotFoundError` when running alembic commands.

### Pitfall 3: Integration Tests Break Due to conftest.py Path Changes
**What goes wrong:** Integration tests can't find fixtures or database configuration.
**Why it happens:** Tests reference `src.adapters.*` imports and the conftest.py fixture hierarchy expects a specific directory layout.
**How to avoid:** After moving tests to `apps/api/tests/`, update all fixture imports. Run the full test suite after each move step.
**Warning signs:** `pytest` collection errors, fixture not found errors.

### Pitfall 4: Docker Volume Mounts Point to Wrong Paths
**What goes wrong:** Devcontainer can't find source code; hot reload doesn't work.
**Why it happens:** Docker volume mounts and working directory assume `src/` is at repo root. After restructure, code is at `apps/api/src/`.
**How to avoid:** The volume mount `.:/workspace:cached` already mounts the entire repo root, so paths within the container just need the subdirectory. Update `uvicorn` startup commands and any path references in docker-compose files. **The decision is to fix only what breaks, not add new features.**
**Warning signs:** Container starts but app can't find modules; file changes don't trigger reload.

### Pitfall 5: import-linter Configuration Breaks After Path Changes
**What goes wrong:** Pre-commit hooks fail on import-linter checks.
**Why it happens:** `tool.importlinter` in pyproject.toml references `root_packages = ["src"]` and specific module paths like `src.domain`, `src.adapters`.
**How to avoid:** Update import-linter configuration to reflect new package structure. The root_packages and contract module paths must match the new layout.
**Warning signs:** `lint-imports` command fails in pre-commit.

### Pitfall 6: Pre-commit Hooks Reference Wrong File Paths
**What goes wrong:** Ruff, mypy, and other pre-commit hooks can't find files or use wrong config.
**Why it happens:** Hooks like ruff and mypy may have source path assumptions (e.g., `source = ["src"]` in coverage config).
**How to avoid:** Update `.pre-commit-config.yaml`, `pyproject.toml` tool configs (ruff, mypy, pytest, coverage, import-linter) to use new paths. Run `pre-commit run --all-files` after restructure.
**Warning signs:** Pre-commit hooks fail on files they should find.

### Pitfall 7: Circular Import When Domain Package Name Conflicts
**What goes wrong:** `from domain.model import Account` resolves to wrong package.
**Why it happens:** If the domain package at `libs/domain/domain/` has the same name as a subdirectory elsewhere, Python's import resolution may pick the wrong one.
**How to avoid:** uv workspace editable installs should make the `domain` package resolve correctly. Verify with `python -c "import domain; print(domain.__file__)"` after setup.
**Warning signs:** Imports resolve to unexpected locations.

## Code Examples

### Nx Workspace Configuration (nx.json)

```json
{
  "$schema": "./node_modules/nx/schemas/nx-schema.json",
  "namedInputs": {
    "pythonSource": ["{projectRoot}/**/*.py"],
    "default": ["{projectRoot}/**/*", "!{projectRoot}/**/*.md"]
  },
  "targetDefaults": {
    "test": {
      "dependsOn": ["^test"],
      "inputs": ["pythonSource"],
      "cache": true
    },
    "lint": {
      "inputs": ["pythonSource"],
      "cache": true
    }
  }
}
```

### git mv Sequence for Incremental Migration

```bash
# Step 1: Move backend to apps/api/
mkdir -p apps/api
git mv src apps/api/src
git mv tests apps/api/tests

# Step 2: Move alembic to apps/api/
git mv alembic apps/api/alembic

# Step 3: Extract domain to libs/domain/
mkdir -p libs/domain
git mv apps/api/src/domain libs/domain/domain
# Move domain unit tests
mkdir -p libs/domain/tests/unit
git mv apps/api/tests/unit/domain libs/domain/tests/unit/domain
```

### Import Rewriting Script Approach

```bash
# Find all files with old imports and rewrite
# In apps/api/ and libs/domain/: src.domain.* -> domain.*
find apps/api libs/domain -name "*.py" -exec \
  sed -i 's/from src\.domain\./from domain./g; s/import src\.domain\./import domain./g' {} +

# Verify no remaining old imports
grep -r "from src\.domain\." apps/ libs/ --include="*.py"
grep -r "import src\.domain\." apps/ libs/ --include="*.py"
```

### Devcontainer Updates (Fix What Breaks)

```json
// .devcontainer/devcontainer.json changes:
// postCreateCommand needs to handle workspace sync
{
  "postCreateCommand": "uv sync && npm ci"
  // This should still work since uv workspace operates from repo root
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| @nxlv/python with Poetry | @nxlv/python with uv support | 2024-2025 | Plugin now supports uv, but adds complexity |
| Manual sys.path for Python monorepos | uv workspaces (`tool.uv.workspace`) | 2024 (uv 0.3+) | Native Python workspace support eliminates sys.path hacks |
| workspace.json (Nx) | nx.json + project.json per project | Nx 15+ | workspace.json deprecated; all config in nx.json + project.json |
| Nx preset=empty | nx init (for existing projects) | Nx 16+ | `nx init` designed for adding to existing repos |

**Deprecated/outdated:**
- `workspace.json`: Replaced by `nx.json` + per-project `project.json` files
- `@nrwl/*` package scope: Renamed to `@nx/*` (though @nxlv/python is a community plugin, not affected)

## Claude's Discretion Recommendations

### Alembic Migrations Location
**Recommendation:** Move to `apps/api/alembic/` with `alembic.ini` staying at repo root.

Rationale: The API app owns the database schema, so migrations belong with the API. However, `alembic.ini` should stay at repo root because developers run `alembic upgrade head` from the workspace root. Configure `script_location = apps/api/alembic` and `prepend_sys_path = apps/api` in `alembic.ini`.

**Confidence:** MEDIUM -- This follows standard monorepo patterns. The `prepend_sys_path` configuration needs testing.

### Python Dependency Management
**Recommendation:** Use uv workspaces with a root pyproject.toml as workspace root and per-project pyproject.toml files.

Structure:
- Root `pyproject.toml`: workspace definition + shared dev dependencies (ruff, pytest, mypy)
- `apps/api/pyproject.toml`: API-specific runtime dependencies + domain workspace dep
- `libs/domain/pyproject.toml`: domain-only dependencies (typeid-python, returns)

The root pyproject.toml acts as the workspace root. Running `uv sync` from repo root installs all workspace members as editable packages.

**Confidence:** MEDIUM -- uv workspace support is mature but we need to verify it works well with Nx and the devcontainer setup.

### Nx Plugin Choices
**Recommendation:** Do NOT use `@nxlv/python`. Use only core Nx with `nx:run-commands`.

Rationale:
1. `@nxlv/python` creates a root `pyproject.toml` that can break non-Python apps (documented issue #258)
2. We already have uv for Python dependency management; adding another abstraction layer is unnecessary
3. `nx:run-commands` covers all needed targets: test (pytest), lint (ruff), serve (uvicorn)
4. The plugin's value-add (dependency bundling, Poetry abstraction) is irrelevant for this project

This means manually creating `project.json` files rather than using generators, which is acceptable given only 4 projects (api, web, domain, ui).

**Confidence:** HIGH -- `nx:run-commands` is well-documented and the simplest path.

### Nx Workspace Configuration
**Recommendation:** Minimal nx.json with targetDefaults for Python projects.

```json
{
  "$schema": "./node_modules/nx/schemas/nx-schema.json",
  "namedInputs": {
    "pythonSource": ["{projectRoot}/**/*.py"]
  },
  "targetDefaults": {
    "test": {
      "cache": true,
      "inputs": ["pythonSource"]
    },
    "lint": {
      "cache": true,
      "inputs": ["pythonSource"]
    }
  }
}
```

**Confidence:** MEDIUM -- targetDefaults syntax is well-documented but caching behavior for Python projects via run-commands needs validation.

## Open Questions

1. **Alembic prepend_sys_path with uv workspaces**
   - What we know: Alembic needs `src.adapters.persistence.orm.base` to be importable from env.py. With uv workspaces, the `domain` package will be editable-installed.
   - What's unclear: Will `prepend_sys_path = apps/api` in alembic.ini work correctly with uv's editable install paths? Or do we need `prepend_sys_path = .` (repo root)?
   - Recommendation: Test both approaches during implementation. Start with `prepend_sys_path = apps/api` and fall back to `.` if needed.

2. **Import-linter with new package structure**
   - What we know: Current config uses `root_packages = ["src"]` and checks `src.domain`, `src.adapters`, `src.application` layers.
   - What's unclear: After extraction, domain is a separate package. Can import-linter enforce cross-package boundaries?
   - Recommendation: Update import-linter to use `root_packages = ["src", "domain"]` and adjust contract definitions. May need separate configs per project.

3. **Test discovery with colocated tests**
   - What we know: Current pytest config uses `testpaths = ["tests"]` and tests import `from src.domain.*`.
   - What's unclear: After splitting tests between `apps/api/tests/` and `libs/domain/tests/`, running `nx run api:test` from `apps/api/` needs the right PYTHONPATH.
   - Recommendation: Each project's pyproject.toml should have its own `[tool.pytest.ini_options]` with correct testpaths. uv workspace editable installs should handle import resolution.

4. **Which domain unit tests belong in libs/domain/tests vs apps/api/tests**
   - What we know: `tests/unit/domain/` tests pure domain logic. `tests/unit/application/` tests services that import both domain and adapters.
   - What's unclear: Should application service tests stay with the API or move with domain?
   - Recommendation: Only pure domain tests (`tests/unit/domain/`) move to `libs/domain/tests/`. Application tests (`tests/unit/application/`) stay with the API since they test API-specific orchestration logic that depends on adapters.

## Sources

### Primary (HIGH confidence)
- Nx official documentation: project configuration, nx.json reference, run-commands executor
  - https://nx.dev/docs/reference/project-configuration
  - https://nx.dev/docs/reference/nx-json
  - https://nx.dev/docs/guides/adopting-nx/adding-to-existing-project
  - https://nx.dev/docs/guides/tasks--caching/run-commands-executor
- uv workspace documentation: https://docs.astral.sh/uv/concepts/projects/workspaces/
- Nx git history preservation: https://nx.dev/docs/guides/adopting-nx/preserving-git-histories

### Secondary (MEDIUM confidence)
- @nxlv/python npm package documentation: https://www.npmjs.com/package/@nxlv/python
- @nxlv/python GitHub issue on root pyproject.toml conflict: https://github.com/lucasvieirasilva/nx-plugins/issues/258
- shadcn/ui monorepo documentation: https://ui.shadcn.com/docs/monorepo
- Nx 2026 roadmap (polyglot improvements): https://nx.dev/blog/nx-2026-roadmap

### Tertiary (LOW confidence)
- Blog posts on Nx + Python monorepos: https://blog.nicoandres.dev/nx-monorepo/
- Blog posts on uv workspaces: https://medium.com/@life-is-short-so-enjoy-it/python-monorepo-with-uv-f4ced6f1f425
- Git mv best practices 2026: https://thelinuxcode.com/git-move-files-practical-renames-refactors-and-history-preservation-in-2026/

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM -- Nx + uv workspaces is the right combination, but the exact interplay between nx:run-commands and uv workspace editable installs needs validation during implementation
- Architecture: MEDIUM -- Directory structure is user-specified and clear; import path strategy is well-understood but the volume of changes (~180 imports, ~60 files) makes execution risky
- Pitfalls: HIGH -- Pitfalls are well-understood from codebase analysis (import paths, alembic, conftest, docker, import-linter, pre-commit)

**Research date:** 2026-02-07
**Valid until:** 2026-03-07 (30 days -- Nx and uv are stable tools)

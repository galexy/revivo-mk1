---
phase: quick
plan: 001
type: execute
wave: 1
depends_on: []
files_modified:
  - CLAUDE.md
  - .claude/agents/gsd-executor.md
  - .claude/agents/gsd-planner.md
autonomous: true

must_haves:
  truths:
    - "CLAUDE.md exists at project root and contains chokepoint testing rules"
    - "Claude Code always sees the chokepoint instructions (CLAUDE.md is auto-loaded)"
    - "GSD executor agent includes service smoke test mandate after migration and endpoint tasks"
    - "GSD planner agent includes guidance to add chokepoint validation tasks to plans"
    - "Phase completion requires actual running service verification"
  artifacts:
    - path: "CLAUDE.md"
      provides: "Project-wide chokepoint testing guardrails"
      contains: "alembic upgrade head"
    - path: ".claude/agents/gsd-executor.md"
      provides: "Executor-level service smoke test mandate"
      contains: "smoke test"
    - path: ".claude/agents/gsd-planner.md"
      provides: "Planner-level chokepoint task guidance"
      contains: "chokepoint"
  key_links:
    - from: "CLAUDE.md"
      to: "Claude Code session"
      via: "Auto-loaded by Claude Code at session start"
      pattern: "CLAUDE\\.md"
    - from: ".claude/agents/gsd-executor.md"
      to: "Plan execution"
      via: "Executor agent reads this as its system prompt"
      pattern: "gsd-executor"
    - from: ".claude/agents/gsd-planner.md"
      to: "Plan creation"
      via: "Planner agent reads this as its system prompt"
      pattern: "gsd-planner"
---

<objective>
Add chokepoint testing guardrails to prevent the recurring pattern where integration tests pass but the actual running service fails. This addresses four specific failure modes: (1) integration tests passing while the real service has 500 errors, (2) FK mismatches between SQLAlchemy models and Alembic migrations, (3) basic scenarios returning 500 ISE due to untested code paths, (4) claiming phase completion when the service does not actually work.

Purpose: Establish permanent project-wide rules that Claude Code always sees, ensuring every future phase includes real service validation at critical points during execution -- not just at the end.

Output: A CLAUDE.md file at the project root with testing guardrails, plus targeted updates to gsd-executor.md and gsd-planner.md agent definitions.
</objective>

<execution_context>
@./.claude/get-shit-done/workflows/execute-plan.md
@./.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
@docker-compose.yml
@tests/integration/conftest.py
@alembic.ini
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create CLAUDE.md with chokepoint testing guardrails</name>
  <files>CLAUDE.md</files>
  <action>
Create a CLAUDE.md file at the project root (/workspace/CLAUDE.md). This file is automatically loaded by Claude Code at the start of every session, so its contents serve as persistent instructions.

The file must contain these sections:

**Project overview** (brief):
- Python FastAPI app with PostgreSQL (SQLAlchemy + Alembic)
- Docker Compose setup: app service + postgres service
- Tests: pytest with unit (tests/unit) and integration (tests/integration) directories
- Integration tests use transactional rollback (session-scoped setup) which can mask issues that only appear with committed data

**Chokepoint Testing Rules** (the core content):

1. **After writing or modifying any Alembic migration:**
   - Run `alembic upgrade head` against the actual dev database (DATABASE_URL_SYNC) and verify it applies cleanly
   - If the migration involves FK constraints, verify the referenced tables/columns exist
   - Run `alembic downgrade -1` then `alembic upgrade head` to verify reversibility
   - NEVER rely solely on integration tests for migration correctness -- integration tests use `metadata.create_all()` which bypasses Alembic entirely

2. **After implementing or modifying API endpoints:**
   - Start the actual service (`uvicorn src.main:app --host 0.0.0.0 --port 8000`) or use Docker Compose
   - Smoke test key endpoints with curl/httpie against the running service
   - Verify at minimum: a successful response (not 500), correct response shape, auth works if required
   - Do NOT skip this step even if integration tests pass -- TestClient may behave differently from a real HTTP server

3. **Integration test awareness:**
   - The test suite uses `metadata.create_all()` (not Alembic migrations) to create tables -- this means the test schema can drift from production schema
   - Tests use transactional rollback per test -- FK constraints, triggers, and sequences may behave differently with committed data
   - When writing tests, consider: "Would this also work against a real database with real migrations?"
   - If a test passes but you suspect it might not work in production, add a comment noting the concern

4. **Phase/wave completion chokepoints:**
   - After completing a wave of tasks that includes migrations: run migrations against real DB, then start the service and smoke test
   - After completing a wave of tasks that includes API endpoints: start the service and verify those endpoints work
   - Before claiming any phase is complete: start the actual service, run through the key user flows for that phase with curl
   - If ANY smoke test fails, the phase is NOT complete -- fix the issue before proceeding

5. **Never claim completion prematurely:**
   - "All tests pass" is necessary but NOT sufficient for phase completion
   - The actual service must start and handle basic requests without 500 errors
   - If there is a gap between what tests verify and what the running service does, close that gap before moving on

**Service testing commands** (reference section):
```bash
# Start service directly
uvicorn src.main:app --host 0.0.0.0 --port 8000 &

# Or via Docker Compose
docker compose up -d app

# Run migrations against real DB
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@postgres:5432/personal_finance alembic upgrade head

# Smoke test examples
curl -s http://localhost:8000/docs | head -5  # OpenAPI docs load
curl -s -X POST http://localhost:8000/auth/token -d "username=test@example.com&password=testpass" -H "Content-Type: application/x-www-form-urlencoded"

# Run all tests
pytest tests/ -x -q
```

**SQLAlchemy/Alembic parity warning:**
```
CRITICAL: tests/integration/conftest.py uses metadata.create_all() which creates tables
from SQLAlchemy table definitions, NOT from Alembic migrations. This means:
- A column added to the SQLAlchemy model but missing from migrations will work in tests but fail in production
- An FK constraint in migrations but missing from SQLAlchemy models will exist in production but not in tests
- Index definitions may differ between the two schemas

Always verify migrations apply cleanly to a real database, not just that tests pass.
```
  </action>
  <verify>
1. File exists at /workspace/CLAUDE.md
2. File contains "alembic upgrade head" (migration verification rule)
3. File contains "metadata.create_all" (schema parity warning)
4. File contains "smoke test" (service verification rule)
5. File contains "Never claim completion" (premature completion prevention)
  </verify>
  <done>CLAUDE.md exists at project root with all five chokepoint testing rule categories and the SQLAlchemy/Alembic parity warning</done>
</task>

<task type="auto">
  <name>Task 2: Update GSD executor and planner agents with chokepoint mandates</name>
  <files>.claude/agents/gsd-executor.md, .claude/agents/gsd-planner.md</files>
  <action>
**Update gsd-executor.md:**

Add a new section `<chokepoint_validation>` after the existing `<deviation_rules>` section (before `<authentication_gates>`). Content:

```xml
<chokepoint_validation>
## Service Smoke Test Mandate

**After completing any task that involves database migrations:**
1. Run `alembic upgrade head` against the actual database and verify it succeeds
2. If it fails, fix the migration before committing the task
3. Track as part of task verification, not as a deviation

**After completing any task that involves API endpoint implementation:**
1. Start the actual service (uvicorn or docker compose)
2. Send at least one request to each new/modified endpoint with curl
3. Verify the response is not a 500 error and has the expected shape
4. Stop the service after verification
5. If the service fails to start or returns 500s, fix before committing

**Before final task in any plan that modifies backend code:**
1. Ensure all migrations apply cleanly (`alembic upgrade head`)
2. Start the service and verify it responds to basic health/docs requests
3. If the plan's success criteria mention specific user flows, test them against the running service

**Integration test vs. production schema awareness:**
- This project's integration tests use `metadata.create_all()` (NOT Alembic migrations)
- A passing test suite does NOT guarantee the real service works
- Always cross-check test results against the actual running service for migration-related changes

**Do NOT claim task/plan completion if:**
- Migrations fail to apply to the real database
- The service returns 500 errors on basic scenarios
- Integration tests pass but the running service behaves differently
</chokepoint_validation>
```

**Update gsd-planner.md:**

Add a new section `<chokepoint_planning>` after the existing `<checkpoints>` section (before `<tdd_integration>`). Content:

```xml
<chokepoint_planning>
## Chokepoint Validation Tasks

When creating plans for phases that involve backend changes (migrations, API endpoints, service logic), include chokepoint validation in task verification criteria.

**For tasks that create/modify Alembic migrations:**
- The task's <verify> must include: "Run `alembic upgrade head` against real database -- migration applies cleanly"
- The task's <done> must include: "Migration verified against actual database (not just metadata.create_all)"

**For tasks that create/modify API endpoints:**
- The task's <verify> must include: "Start service and curl the new endpoint(s) -- response is not 500"
- The task's <done> must include: "Endpoint verified against running service (not just TestClient)"

**For the final task in any phase with backend changes:**
- Add explicit verification: "Start actual service, run key user flows with curl, verify no 500 errors"
- This is NOT optional -- integration tests alone are insufficient due to schema parity gaps

**Anti-pattern to prevent:**
Integration tests use `metadata.create_all()` which bypasses Alembic. A FK mismatch between SQLAlchemy models and Alembic migrations will cause tests to pass but the real service to fail. Plans must account for this gap.

**When estimating task scope:**
- Add ~5 minutes per migration task for real-DB verification
- Add ~5 minutes per endpoint task for service smoke testing
- These are not overhead -- they prevent multi-hour debugging sessions later
</chokepoint_planning>
```
  </action>
  <verify>
1. gsd-executor.md contains the `<chokepoint_validation>` section
2. gsd-executor.md mentions "alembic upgrade head" and "smoke test" in the new section
3. gsd-planner.md contains the `<chokepoint_planning>` section
4. gsd-planner.md mentions "chokepoint" and "metadata.create_all" in the new section
5. Both files remain valid (no broken XML structure, existing sections intact)
  </verify>
  <done>Both GSD agent definitions updated with chokepoint validation mandates. Executor knows to smoke test after migrations and endpoints. Planner knows to include chokepoint verification in task specs.</done>
</task>

</tasks>

<verification>
1. /workspace/CLAUDE.md exists and contains all chokepoint testing rules
2. /workspace/.claude/agents/gsd-executor.md has `<chokepoint_validation>` section
3. /workspace/.claude/agents/gsd-planner.md has `<chokepoint_planning>` section
4. No existing functionality in the agent files is broken (sections above and below the insertions are intact)
</verification>

<success_criteria>
1. CLAUDE.md at project root contains five categories of chokepoint testing rules
2. CLAUDE.md contains the SQLAlchemy/Alembic parity warning with specific explanation of metadata.create_all vs Alembic divergence
3. GSD executor agent includes mandatory service smoke testing after migration and endpoint tasks
4. GSD planner agent includes guidance to add chokepoint verification to plan task specs
5. All three files are syntactically valid and do not break existing workflows
</success_criteria>

<output>
After completion, create `.planning/quick/001-add-chokepoint-testing-guardrails/001-SUMMARY.md`
</output>

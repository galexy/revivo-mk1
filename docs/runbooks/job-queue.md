# Job Queue Operations Runbook

This runbook covers operational procedures for the Procrastinate-based job queue.

## Overview

The job queue handles async side effects (email sending, external API calls) triggered by domain events. It uses:
- **Procrastinate** - PostgreSQL-based job queue
- **Separate database** - `postgres-jobs` service, not the main app database
- **In-process worker** - runs alongside FastAPI via lifespan

## Quick Reference

| Task | Command |
|------|---------|
| View queue stats | `./scripts/jobs/queue-stats.sh` |
| List failed jobs | `./scripts/jobs/list-failed.sh` |
| Get job details | `./scripts/jobs/job-status.sh <id>` |
| Retry single job | `./scripts/jobs/retry-job.sh <id>` |
| Retry all failed | `./scripts/jobs/retry-all-failed.sh [queue]` |
| Purge old jobs | `./scripts/jobs/purge-old.sh <days>` |
| Apply schema | `./scripts/jobs/apply-schema.sh` |

## Environment Setup

Scripts require `JOB_QUEUE_DATABASE_URL` environment variable:

```bash
export JOB_QUEUE_DATABASE_URL="postgresql://postgres:postgres@localhost:5433/jobs"
```

In docker-compose, this is set automatically for the app service.

## Common Procedures

### 1. Check Queue Health

Run daily or when investigating issues:

```bash
./scripts/jobs/queue-stats.sh
```

**Healthy indicators:**
- No jobs stuck in `doing` status for >5 minutes
- Failed job count stable (not growing)
- Succeeded jobs being processed

**Warning signs:**
- Growing backlog of `todo` jobs
- Jobs stuck in `doing` (worker may have crashed)
- Spike in failed jobs

### 2. Investigate Failed Jobs

When you see failed jobs:

```bash
# List recent failures
./scripts/jobs/list-failed.sh

# Get details on a specific job
./scripts/jobs/job-status.sh 123
```

**Common failure patterns:**

| Error | Likely Cause | Fix |
|-------|--------------|-----|
| `ConnectionError` | External service down | Wait and retry |
| `TimeoutError` | Service slow/overloaded | Retry with backoff |
| `ValidationError` | Bad job arguments | Check event payload, may need code fix |
| `DatabaseError` | DB connection issue | Check postgres-jobs health |

### 3. Retry Failed Jobs

After fixing the root cause:

```bash
# Retry a single job
./scripts/jobs/retry-job.sh 123

# Retry all failed jobs in a queue
./scripts/jobs/retry-all-failed.sh email

# Retry ALL failed jobs (use carefully)
./scripts/jobs/retry-all-failed.sh
```

### 4. Manual Job Inspection

For deep debugging, use Procrastinate shell:

```bash
procrastinate --app=src.adapters.jobs.app.job_queue shell
```

Or connect directly to the jobs database:

```bash
psql $JOB_QUEUE_DATABASE_URL
```

Useful queries:

```sql
-- Jobs stuck in 'doing' for >5 minutes (potentially stalled)
SELECT * FROM procrastinate_jobs
WHERE status = 'doing'
  AND started_at < NOW() - INTERVAL '5 minutes';

-- Recent errors by type
SELECT
    task_name,
    error,
    COUNT(*)
FROM procrastinate_jobs j
JOIN procrastinate_events e ON j.id = e.job_id
WHERE e.type = 'error'
  AND e.at > NOW() - INTERVAL '1 hour'
GROUP BY task_name, error;
```

### 5. Maintenance: Purge Old Jobs

Run weekly or monthly to prevent table bloat:

```bash
# Purge succeeded jobs older than 30 days
./scripts/jobs/purge-old.sh 30

# Also purge old failed jobs (after investigation)
./scripts/jobs/purge-old.sh 90 --include-failed
```

**Recommendation:**
- Keep succeeded jobs: 30 days
- Keep failed jobs: 90 days (for debugging patterns)

## Troubleshooting

### Worker Not Processing Jobs

**Symptoms:** Jobs stuck in `todo`, no progress

**Checks:**
1. Is the API service running? (worker runs in same process)
2. Check logs for worker startup: `"job_queue_worker_started"`
3. Check for connection errors to postgres-jobs

**Fix:**
- Restart the API service
- Verify `JOB_QUEUE_DATABASE_URL` is correct
- Check postgres-jobs is healthy: `docker compose ps postgres-jobs`

### Jobs Failing Repeatedly

**Symptoms:** Same job fails, retries, fails again

**Checks:**
1. Get job details: `./scripts/jobs/job-status.sh <id>`
2. Check error_traceback for root cause
3. Check if external service is down

**Fix:**
- If transient: wait for retries to succeed
- If permanent: fix code, then retry job
- If bad data: may need to manually mark as succeeded or delete

### Database Connection Issues

**Symptoms:** `could not connect to server` errors

**Checks:**
1. Is postgres-jobs running? `docker compose ps postgres-jobs`
2. Is the port correct? (5433 for jobs DB, 5432 for main DB)
3. Network connectivity between containers

**Fix:**
```bash
# Restart jobs database
docker compose restart postgres-jobs

# Check logs
docker compose logs postgres-jobs
```

### Schema Not Applied

**Symptoms:** `relation "procrastinate_jobs" does not exist`

**Fix:**
```bash
./scripts/jobs/apply-schema.sh
```

This should be run once when setting up a new environment.

## Monitoring Queries

For integration with monitoring systems (Grafana, etc.):

```sql
-- Failed jobs in last hour (for alerting)
SELECT COUNT(*) FROM procrastinate_jobs
WHERE status = 'failed'
  AND created_at > NOW() - INTERVAL '1 hour';

-- Queue depth by queue (for dashboards)
SELECT queue_name, COUNT(*) as pending
FROM procrastinate_jobs
WHERE status = 'todo'
GROUP BY queue_name;

-- Processing rate (jobs/hour)
SELECT COUNT(*) as processed_last_hour
FROM procrastinate_jobs
WHERE status = 'succeeded'
  AND created_at > NOW() - INTERVAL '1 hour';

-- Average processing time by task
SELECT
    task_name,
    AVG(EXTRACT(EPOCH FROM (finished_at - started_at))) as avg_duration_seconds
FROM procrastinate_jobs
WHERE status = 'succeeded'
  AND finished_at IS NOT NULL
GROUP BY task_name;
```

## Emergency Procedures

### Stop All Job Processing

If jobs are causing problems and need to stop immediately:

```bash
# Restart API without worker (temporary)
# Set environment variable to skip worker startup
JOB_QUEUE_ENABLED=false uvicorn src.adapters.api.app:app
```

Or stop the API service entirely.

### Clear All Pending Jobs

**Use with extreme caution** - jobs will be lost:

```sql
DELETE FROM procrastinate_jobs WHERE status = 'todo';
```

### Reset a Stuck Job

If a job is stuck in `doing` (worker crashed mid-processing):

```sql
UPDATE procrastinate_jobs
SET status = 'todo', started_at = NULL
WHERE id = <job_id> AND status = 'doing';
```

### Bulk Reset Stuck Jobs

If multiple jobs are stuck in `doing` after a crash:

```sql
UPDATE procrastinate_jobs
SET status = 'todo', started_at = NULL
WHERE status = 'doing'
  AND started_at < NOW() - INTERVAL '10 minutes';
```

## Architecture Notes

- **Event bus** dispatches domain events synchronously after UoW commit
- **Event handlers** enqueue jobs for async processing
- **Jobs database** is separate from main app database (isolation)
- **Retries** use exponential backoff (configurable per task)
- **Failed jobs** stay in database for debugging (not auto-deleted)
- **Worker** runs in the same process as FastAPI via lifespan context

### Job Lifecycle

```
todo -> doing -> succeeded
              -> failed (after max retries)
```

### Database Schema

Key tables managed by Procrastinate:
- `procrastinate_jobs` - job queue with status, args, scheduling
- `procrastinate_events` - event log including errors and tracebacks

## Related Documentation

- [Procrastinate Docs](https://procrastinate.readthedocs.io/)
- Phase 5 Research: `.planning/phases/05-domain-event-publishing/05-RESEARCH.md`
- Phase 5 Context: `.planning/phases/05-domain-event-publishing/05-CONTEXT.md`

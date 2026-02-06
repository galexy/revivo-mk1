#!/usr/bin/env bash
# Get detailed status of a specific job
# Usage: ./job-status.sh <job_id>
set -euo pipefail

JOB_ID="${1:?Usage: ./job-status.sh <job_id>}"

cat << SQL | psql "$JOB_QUEUE_DATABASE_URL" -x
SELECT
    j.id,
    j.queue_name,
    j.task_name,
    j.status,
    j.args,
    j.created_at,
    j.scheduled_at,
    j.started_at,
    j.attempts,
    e.error,
    e.error_traceback
FROM procrastinate_jobs j
LEFT JOIN procrastinate_events e ON j.id = e.job_id AND e.type = 'error'
WHERE j.id = $JOB_ID
ORDER BY e.at DESC
LIMIT 1;
SQL

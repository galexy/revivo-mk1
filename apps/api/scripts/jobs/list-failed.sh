#!/usr/bin/env bash
# List failed jobs with error information
# Usage: ./list-failed.sh [limit]
set -euo pipefail

LIMIT="${1:-20}"

cat << SQL | psql "$JOB_QUEUE_DATABASE_URL" -t
SELECT
    id,
    queue_name,
    task_name,
    created_at,
    attempts,
    scheduled_at
FROM procrastinate_jobs
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT $LIMIT;
SQL

echo ""
echo "To see error details for a job: ./job-status.sh <job_id>"

#!/usr/bin/env bash
# Retry a specific failed job
# Usage: ./retry-job.sh <job_id>
set -euo pipefail

JOB_ID="${1:?Usage: ./retry-job.sh <job_id>}"

echo "Retrying job ${JOB_ID}..."

cat << SQL | psql "$JOB_QUEUE_DATABASE_URL"
UPDATE procrastinate_jobs
SET status = 'todo', scheduled_at = NOW()
WHERE id = $JOB_ID AND status = 'failed';
SQL

echo "Job ${JOB_ID} queued for retry."

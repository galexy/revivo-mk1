#!/usr/bin/env bash
# Retry all failed jobs in a queue
# Usage: ./retry-all-failed.sh [queue_name]
set -euo pipefail

QUEUE="${1:-}"

if [ -z "$QUEUE" ]; then
    echo "Retrying ALL failed jobs..."
    cat << 'SQL' | psql "$JOB_QUEUE_DATABASE_URL"
UPDATE procrastinate_jobs
SET status = 'todo', scheduled_at = NOW()
WHERE status = 'failed';
SQL
else
    echo "Retrying failed jobs in queue: ${QUEUE}..."
    psql "$JOB_QUEUE_DATABASE_URL" -c "UPDATE procrastinate_jobs SET status = 'todo', scheduled_at = NOW() WHERE status = 'failed' AND queue_name = '$QUEUE';"
fi

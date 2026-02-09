#!/usr/bin/env bash
# Purge completed jobs older than N days
# Usage: ./purge-old.sh <days> [--include-failed]
set -euo pipefail

DAYS="${1:?Usage: ./purge-old.sh <days> [--include-failed]}"
INCLUDE_FAILED="${2:-}"

echo "Purging jobs older than ${DAYS} days..."

if [ "$INCLUDE_FAILED" = "--include-failed" ]; then
    echo "Including failed jobs in purge."
    psql "$JOB_QUEUE_DATABASE_URL" -c "DELETE FROM procrastinate_jobs WHERE (status = 'succeeded' OR status = 'failed') AND created_at < NOW() - INTERVAL '$DAYS days';"
else
    echo "Only purging succeeded jobs (use --include-failed to also purge failed)."
    psql "$JOB_QUEUE_DATABASE_URL" -c "DELETE FROM procrastinate_jobs WHERE status = 'succeeded' AND created_at < NOW() - INTERVAL '$DAYS days';"
fi

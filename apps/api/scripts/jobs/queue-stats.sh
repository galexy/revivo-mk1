#!/usr/bin/env bash
# Show job queue statistics
# Usage: ./queue-stats.sh
set -euo pipefail

echo "=== Job Queue Statistics ==="
echo ""

cat << 'SQL' | psql "$JOB_QUEUE_DATABASE_URL" -t
SELECT
    queue_name,
    status,
    COUNT(*) as count
FROM procrastinate_jobs
GROUP BY queue_name, status
ORDER BY queue_name, status;
SQL

echo ""
echo "=== Recent Failures (last 24h) ==="

cat << 'SQL' | psql "$JOB_QUEUE_DATABASE_URL" -t
SELECT
    task_name,
    COUNT(*) as failures
FROM procrastinate_jobs
WHERE status = 'failed'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY task_name
ORDER BY failures DESC;
SQL

#!/usr/bin/env bash
# Apply Procrastinate schema to jobs database
# Run this before starting workers for the first time
set -euo pipefail

echo "Applying Procrastinate schema to jobs database..."
procrastinate --app=src.adapters.jobs.app.job_queue schema --apply
echo "Schema applied successfully."

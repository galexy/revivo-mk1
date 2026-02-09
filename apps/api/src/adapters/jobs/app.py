"""Procrastinate job queue application.

Uses a separate PostgreSQL database from the main app as per
architecture decisions. Connection via JOB_QUEUE_DATABASE_URL.
"""

import os

from procrastinate import App, PsycopgConnector


def create_job_queue() -> App:
    """Create and configure Procrastinate job queue app.

    Uses a separate database from the main app as per CONTEXT.md decisions.
    Connection string from JOB_QUEUE_DATABASE_URL environment variable.

    Returns:
        Configured Procrastinate App instance
    """
    conninfo = os.getenv(
        "JOB_QUEUE_DATABASE_URL",
        "postgresql://postgres:postgres@postgres-jobs:5432/jobs",
    )

    return App(
        connector=PsycopgConnector(conninfo=conninfo),
        import_paths=["src.adapters.jobs.tasks"],
    )


# Singleton instance
job_queue = create_job_queue()

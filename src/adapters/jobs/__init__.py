"""Job queue infrastructure using Procrastinate.

Provides async job processing for side effects like email sending,
external API calls, and other potentially-failing operations.
"""

from .app import job_queue

__all__ = ["job_queue"]

"""Domain ports - interfaces for infrastructure adapters.

Ports define the contracts that infrastructure must implement.
This enables dependency inversion: the domain defines what it needs,
and infrastructure adapters implement those interfaces.

Key ports:
- Repository: Persistence of aggregates
- UnitOfWork: Transaction boundary management
- EmailService: Transactional email delivery
"""

from src.domain.ports.email_service import EmailDeliveryError, EmailService
from src.domain.ports.repository import Repository
from src.domain.ports.unit_of_work import UnitOfWork

__all__ = [
    "EmailDeliveryError",
    "EmailService",
    "Repository",
    "UnitOfWork",
]

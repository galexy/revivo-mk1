"""Shared pytest fixtures and hypothesis configuration.

This module provides common test fixtures and configures hypothesis
for property-based testing with CI-friendly settings.
"""

import pytest
from decimal import Decimal
from hypothesis import settings, Verbosity

# Configure hypothesis profiles for different environments
# CI profile: More thorough testing with 200 examples
settings.register_profile("ci", max_examples=200, deadline=None)
# Dev profile: Faster feedback with 50 examples
settings.register_profile("dev", max_examples=50, deadline=None)


@pytest.fixture
def usd_100() -> "Money":
    """Create a Money instance for $100 USD."""
    from src.domain.model.money import Money

    return Money(Decimal("100.00"), "USD")


@pytest.fixture
def usd_50() -> "Money":
    """Create a Money instance for $50 USD."""
    from src.domain.model.money import Money

    return Money(Decimal("50.00"), "USD")


@pytest.fixture
def eur_100() -> "Money":
    """Create a Money instance for 100 EUR."""
    from src.domain.model.money import Money

    return Money(Decimal("100.00"), "EUR")

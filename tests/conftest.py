"""Common fixtures for the Leslie's Pool Water Tests tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let the HA test harness find the integration under custom_components/."""
    yield


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Stub the integration's async_setup_entry so flow tests don't load sensors."""
    with patch(
        "custom_components.leslies_pool.async_setup_entry", return_value=True
    ) as m:
        yield m

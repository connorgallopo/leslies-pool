"""Common fixtures for the Leslie's Pool Water Tests tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.leslies_pool.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry

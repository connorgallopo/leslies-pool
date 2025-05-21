"""Test the Leslie's Pool Water Tests date parsing."""

from datetime import datetime

import pytest
from homeassistant.components.leslies_pool.sensor import parse_test_date


def test_parse_test_date_valid():
    """Test parsing valid date strings."""
    # Test valid date format
    result = parse_test_date("05/21/2025")
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 5
    assert result.day == 21
    assert result.hour == 12
    assert result.minute == 0
    assert result.second == 0
    assert result.microsecond == 0


def test_parse_test_date_invalid():
    """Test parsing invalid date strings."""
    # Test invalid format
    result = parse_test_date("2025-05-21")
    assert result is None
    
    # Test empty string
    result = parse_test_date("")
    assert result is None
    
    # Test None
    result = parse_test_date(None)
    assert result is None


def test_parse_test_date_edge_cases():
    """Test edge cases for date parsing."""
    # Test date at start of year
    result = parse_test_date("01/01/2025")
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 1
    
    # Test date at end of year
    result = parse_test_date("12/31/2025")
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 12
    assert result.day == 31

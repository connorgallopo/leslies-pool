"""Test the API for Leslie's Pool Water Tests."""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from custom_components.leslies_pool.api import (
    InvalidAuthError,
    LesliesPoolApi,
    PoolNotFoundError,
)


SAMPLE_HISTORY = {
    "water_test_history": {
        "water_tests": [
            {
                "water_test_type": "Free Chlorine",
                "water_test_values": [
                    {
                        "timestamp": "20260509 195323.647",
                        "value": 0.09,
                        "is_store_test": True,
                        "results_id": "48255556",
                    },
                ],
            },
            {
                "water_test_type": "pH",
                "water_test_values": [
                    {
                        "timestamp": "20260509 195323.647",
                        "value": 8.4,
                        "is_store_test": True,
                        "results_id": "48255556",
                    },
                ],
            },
            {
                "water_test_type": "Salt",
                "water_test_values": [
                    {
                        "timestamp": "20260509 195323.647",
                        "value": 2637,
                        "is_store_test": True,
                        "results_id": "48255556",
                    },
                ],
            },
        ],
    },
}

SAMPLE_HOME = {
    "pool_profile": [
        {
            "id": "5891278",
            "pool_name": "Pool",
            "size_in_gallons": "30000",
            "sanitization": "9",
        }
    ]
}

SAMPLE_SANITIZERS = {
    "pool_sanitizers": [
        {"brand_id": "8", "brand_name": "Salt 3000-4000"},
        {"brand_id": "9", "brand_name": "Salt 3000-4500"},
    ]
}

SAMPLE_DAYS_SINCE = {"no_of_days_since_last_watertest": 3}


def _mock_response(status: int = 200, json_data: dict | None = None, headers: dict | None = None):
    m = MagicMock()
    m.status_code = status
    m.json.return_value = json_data or {}
    m.headers = headers or {}
    m.raise_for_status = MagicMock()
    if status >= 400:
        m.raise_for_status.side_effect = Exception(f"HTTP {status}")
    return m


class TestResolveRelateCustomerId(unittest.TestCase):
    """OCAPI Session Bridge: email/password -> (customer_id, relateCustomerID)."""

    @patch("custom_components.leslies_pool.api.requests.get")
    @patch("custom_components.leslies_pool.api.requests.post")
    def test_success(self, mock_post, mock_get):
        mock_post.return_value = _mock_response(
            200,
            {"customer_id": "abc123"},
            headers={"Authorization": "Bearer some.jwt.token"},
        )
        mock_get.return_value = _mock_response(
            200, {"c_relateCustomerID": "15382105"}
        )

        customer_id, relate_id = LesliesPoolApi.resolve_relate_customer_id(
            "user@example.com", "pw"
        )

        assert customer_id == "abc123"
        assert relate_id == "15382105"

    @patch("custom_components.leslies_pool.api.requests.post")
    def test_bad_credentials(self, mock_post):
        mock_post.return_value = _mock_response(401)
        with pytest.raises(InvalidAuthError):
            LesliesPoolApi.resolve_relate_customer_id("user@example.com", "wrong")


class TestDiscoverPoolProfiles(unittest.TestCase):
    """Boomi /poolProfiles/v1 listing."""

    @patch("custom_components.leslies_pool.api.requests.get")
    def test_returns_pools(self, mock_get):
        mock_get.return_value = _mock_response(
            200,
            {
                "pool_profiles": [
                    {"id": "5891278", "pool_name": "Backyard"},
                    {"id": "5891279", "pool_name": "Spa"},
                ]
            },
        )

        pools = LesliesPoolApi.discover_pool_profiles(
            "user@example.com", "15382105"
        )

        assert len(pools) == 2
        assert pools[0].id == "5891278"
        assert pools[0].pool_name == "Backyard"

    @patch("custom_components.leslies_pool.api.requests.get")
    def test_no_pools(self, mock_get):
        mock_get.return_value = _mock_response(200, {"pool_profiles": []})
        with pytest.raises(PoolNotFoundError):
            LesliesPoolApi.discover_pool_profiles("user@example.com", "15382105")


class TestFetchWaterTestData(unittest.TestCase):
    """Runtime fetch: home + history + days-since."""

    def setUp(self):
        self.api = LesliesPoolApi(
            relate_customer_id="15382105",
            email="user@example.com",
            pool_profile_id="5891278",
            pool_name="Pool",
        )

    def _wire_session(self, mock_session_get):
        # The api makes three GETs in this order: home, history, days-since.
        # poolSanitizers is fetched lazily on first sanitizer lookup.
        mock_session_get.side_effect = [
            _mock_response(200, SAMPLE_HOME),
            _mock_response(200, SAMPLE_HISTORY),
            _mock_response(200, SAMPLE_DAYS_SINCE),
            _mock_response(200, SAMPLE_SANITIZERS),
        ]

    def test_happy_path(self):
        with patch.object(self.api, "_session") as mock_session:
            self._wire_session(mock_session.get)
            data = self.api.fetch_water_test_data()

        assert data["free_chlorine"] == 0.09
        assert data["ph"] == 8.4
        assert data["salt"] == 2637
        assert data["test_date"] == "05/09/2026"
        assert data["in_store"] is True
        assert data["test_source"] == "In-Store"
        assert data["results_id"] == "48255556"
        assert data["days_since_test"] == 3
        assert data["sanitizer"] == "Salt 3000-4500"
        assert data["pool_size"] == 30000
        assert data["pool_name_sensor"] == "Pool"

    def test_missing_chemistry_keys_are_none(self):
        """Test types not in the API response come back as None, not KeyError."""
        with patch.object(self.api, "_session") as mock_session:
            self._wire_session(mock_session.get)
            data = self.api.fetch_water_test_data()

        # Bromine isn't in SAMPLE_HISTORY; should be None.
        assert data["bromine"] is None
        assert data["biguanides"] is None

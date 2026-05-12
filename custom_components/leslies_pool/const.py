"""Constants for the Leslie's Pool Water Tests integration."""

from __future__ import annotations

DOMAIN = "leslies_pool"
DATA_UPDATE_INTERVAL = 300

# Boomi mobile-app API. These credentials are baked into Leslie's official
# mobile app (com.lesliespool.mobile, v10.8, ProdEnvironment). They identify
# the app, not the user.
BOOMI_BASE_URL = "https://api.lesl.cloud"
BOOMI_BASIC_USER = "MobileApp@lesliespoolmart-N83JU5"
BOOMI_BASIC_PASS = "7cfa5832-d2ba-4997-adb7-2e2d81ccef96"

# OCAPI Shop API. Used once at setup to look up the user's relateCustomerID
# from their email/password. After that, the relateCustomerID is sent on
# every Boomi call as the DDP_ID header.
OCAPI_BASE_URL = "https://lesliespool.com/s/lpm_site/dw/shop/v23_2"
OCAPI_CLIENT_ID = "a233c1f2-f115-434d-959e-efc789d0cd45"

USER_AGENT = "LesliesPoolCare/10.8 CFNetwork/1410.0.3 Darwin/22.6.0"

# (api_type, sensor_key, display_name, unit)
CHEMISTRY_TESTS: list[tuple[str, str, str, str | None]] = [
    ("Free Chlorine",  "free_chlorine",  "Free Chlorine",    "ppm"),
    ("Total Chlorine", "total_chlorine", "Total Chlorine",   "ppm"),
    ("pH",             "ph",             "pH",               "pH"),
    ("Alkalinity",     "alkalinity",     "Total Alkalinity", "ppm"),
    ("Calcium",        "calcium",        "Calcium Hardness", "ppm"),
    ("Cyanuric Acid",  "cyanuric_acid",  "Cyanuric Acid",    "ppm"),
    ("Iron",           "iron",           "Iron",             "ppm"),
    ("Copper",         "copper",         "Copper",           "ppm"),
    ("Phosphates",     "phosphates",     "Phosphates",       "ppb"),
    ("Salt",           "salt",           "Salt",             "ppm"),
    ("TDS",            "tds",            "TDS",              "ppm"),
    ("Bromine",        "bromine",        "Bromine",          "ppm"),
    ("Biguanides",     "biguanides",     "Biguanides",       "ppm"),
]

# (sensor_key, display_name, unit)
META_SENSORS: list[tuple[str, str, str | None]] = [
    ("test_date",        "Last Tested",          None),
    ("in_store",         "In Store",             None),
    ("test_source",      "Test Source",          None),
    ("days_since_test",  "Days Since Last Test", "d"),
    ("results_id",       "Last Test ID",         None),
    ("sanitizer",        "Pool Sanitizer",       None),
    ("pool_size",        "Pool Size",            "gal"),
    ("pool_name_sensor", "Pool Name",            None),
]

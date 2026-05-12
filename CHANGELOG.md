# Changelog

## 3.0.0 (2026-05-11)

### Features
- Switched from web scraping to the mobile app's JSON API. The previous storefront flow stopped working in mid-2025 when Leslie's added session scoring to the water-test endpoints.
- New setup flow: just email and password. Pool ID and pool name are discovered automatically.
- If your account has more than one pool, a second step lets you pick which one to track.
- Pool sanitizer is now derived from your actual pool profile (e.g. "Salt 3000-4500"), not hardcoded.
- New sensors: TDS, Bromine, Biguanides, Days Since Last Test, Test Source ("In-Store" / "AccuBlue Home"), Last Test ID, Pool Sanitizer, Pool Size, Pool Name.
- Every sensor now carries `results_id`, `test_source`, and `test_timestamp` as state attributes so automations can fire when a new test arrives.
- Sensor names drop the `Leslies` prefix and use HA's `has_entity_name` instead, so they render as `Leslie's Pool - Pool Free Chlorine` etc. under the device.

### Bug Fixes
- Stale data: hardcoded sanitizer `Salt 3000-4000` no longer breaks fetches for accounts with a different sanitizer.

### Migration
- Existing 2.x config entries are migrated automatically on first load. Sensor unique IDs are preserved, so history sticks around.
- Dropped `beautifulsoup4` dependency. Bumped `homeassistant` and `pytest-homeassistant-custom-component`.

## 2.0.1 (2025-05-22)

### Bug Fixes
- Improved session management and authentication handling
- Added detection for login redirects with the `login?rurl=1` pattern
- Added JSON response validation and error handling
- Implemented a cache system for data persistence during API outages
- Fixed sensors to ensure values update properly in Home Assistant history
- Enhanced logging for better troubleshooting

## 2.0.0 (Initial Release)

### Features
- Initial release of the Leslie's Pool integration
- Support for monitoring pool water test data from Leslie's Pool
- Display values for free chlorine, total chlorine, pH, alkalinity, calcium, cyanuric acid, iron, copper, phosphates, and salt
- Show when tests were performed and whether they were in-store tests

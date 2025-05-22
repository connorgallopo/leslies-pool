# Changelog

## 2.0.1 (2025-05-22)

### 🐛 Bug Fixes
- Improved session management and authentication handling
- Added detection for login redirects with the `login?rurl=1` pattern
- Added JSON response validation and error handling
- Implemented a cache system for data persistence during API outages
- Fixed sensors to ensure values update properly in Home Assistant history
- Enhanced logging for better troubleshooting

## 2.0.0 (Initial Release)

### ✨ Features
- Initial release of the Leslie's Pool integration
- Support for monitoring pool water test data from Leslie's Pool
- Display values for free chlorine, total chlorine, pH, alkalinity, calcium, cyanuric acid, iron, copper, phosphates, and salt
- Show when tests were performed and whether they were in-store tests

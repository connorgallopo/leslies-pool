# Leslies Pool Water Test Results

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

**This integration pulls your pool chemistry results from Leslie's Pool and exposes them to Home Assistant. It works for both Leslie's in-store tests and AccuBlue Home tester results.**

**This component will set up the following platforms.**

| Platform | Description                      |
| -------- | -------------------------------- |
| `sensor` | Show info from leslies_pool API. |

**The component will set up the following sensors:**

Chemistry (PPM unless noted):

- Free Chlorine
- Total Chlorine
- pH
- Total Alkalinity
- Calcium Hardness
- Cyanuric Acid
- Iron
- Copper
- Phosphates (PPB)
- Salt
- TDS
- Bromine
- Biguanides

Test metadata:

- Last Tested - Date
- In Store - True/False
- Test Source - "In-Store" or "AccuBlue Home"
- Days Since Last Test
- Last Test ID
- Pool Sanitizer (e.g. "Salt 3000-4500")
- Pool Size (gallons)
- Pool Name

Each sensor also carries `results_id`, `test_source`, and `test_timestamp` as state attributes so automations can fire when a new test arrives.

## Installation - Automatic (REQUIRES HACS)

1. Add this repository URL to HACS custom repositories as an Integration
2. Search for "Leslies" and install the integration
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "leslies_pool"
4. Follow config flow

## Installation - Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `leslies_pool`.
4. Download _all_ the files from the `custom_components/leslies_pool/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "leslies_pool"

## Setup

1. Enter the email and password for your Leslie's account.
2. If your account has more than one pool, pick which one to track.
3. Set a polling rate (seconds).

Your credentials are used once to look up your customer ID and pool list. After that, only the customer ID is sent on data fetches.

## Upgrading from 2.x

3.0 swaps the old HTML-scraping flow for the mobile app's JSON API. The web scraping stopped working in mid-2025 when Leslie's added session scoring to the storefront water-test endpoints.

If you already have an entry configured, the integration migrates it automatically on first load - no manual reconfigure needed. Existing sensor history is preserved (unique IDs are unchanged).

The displayed sensor names drop the `Leslies` prefix since the device name already provides that context. If your dashboards reference entity IDs (e.g. `sensor.leslies_free_chlorine`), those still work.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/connorgallopo
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/connorgallopo/leslies-pool.svg?style=for-the-badge
[commits]: https://github.com/connorgallopo/leslies-pool/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/connorgallopo/leslies-pool.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40connorgallopo-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/connorgallopo/leslies-pool.svg?style=for-the-badge
[releases]: https://github.com/connorgallopo/leslies-pool/releases
[user_profile]: https://github.com/connorgallopo

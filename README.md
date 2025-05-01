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

**This integration leverages Leslie's Pools chemical results internal API to get those results and expose them to HomeAssistant. This will fetch data for both Leslies in-store tests as well as the test results from the AccuBlue home tester.**

**This component will set up the following platforms.**

| Platform | Description                      |
| -------- | -------------------------------- |
| `sensor` | Show info from leslies_pool API. |

**The component will set up the following sensors:**

- Leslies Free Chlorine - PPM
- Leslies Total Chlorine - PPM
- Leslies PH - pH
- Leslies Alkalinity - PPM
- Leslies Calcium - PPM
- Leslies Cyanuric Acid - PPM
- Leslies Iron - PPM
- Leslies Copper - PPM
- Leslies Phosphates - PPB
- Leslies Salt - PPM
- Leslies Last Tested - Date
- Leslies In Store - True/False

## Installation - Automatic (REQUIRES HACS)

1. Add this repository URL to HACS custom repositories as an Integration
2. Search for "Leslies" and install the integration
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "leslies_pool"
4. Follow config flow

## Installation - Manaul

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `leslies_pool`.
4. Download _all_ the files from the `custom_components/leslies_pool/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "leslies_pool"

## Setup

1. Provide the Username and Password for your leslie's account. These are used to auth and refresh cookies
2. Input the Water Test URL. This can be found by navigating [here](https://lesliespool.com/on/demandware.store/Sites-lpm_site-Site/en_US/PoolProfile-Landing) once logged in, and then by clicking on "Water Tests" for the pool you want to integrate. The water test URL can be copied from the URL bar once you have navigated there. This URL contains the Pool ID and Pool Name which are needed to make the API calls to fetch the data.
3. Set a polling rate (Seconds).

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

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## [2.0.1] - 2025-09-15

-   Add specific testing for Wagtail 7.1

## [2.0.0] - 2025-06-05

-   Update Braintree JS SDK from 3.76.4 to 3.120.2 depending on how the FE is implemented in a project this could be a breaking change.

## [1.9.6] - 2025-06-04

-   Add support & testing for Wagtail 7.0

## [1.9.5] - 2025-03-24

-   Add specific testing for Wagtail 6.4

## [1.9.4] - 2024-12-17

-   Add support for Wagtail 6.3
-   Add support for Django 5.1
-   Remove testing for Python 3.8
-   Add testing for Python 3.13
-   Remove testing Wagtail 6.0 and 6.1

## [1.9.3] - 2024-09-06

-   Allow Wagtail 6.2

## [1.9.2] - 2024-06-26

-   Add support for Wagtail 6.1
-   Drop support for Django < 4.2
-   Remove testing for Django 3.2

## [1.9.1] - 2024-04-29

-   Fix missing menu item icons

## [1.9.0] - 2024-03-11

-   Add support for Wagtail 6.0
-   Add support for Django 5.0
-   Remove testing for Wagtail 4.1
-   Drop support for Wagtail < 5.2

## [1.8.1] - 2023-11-29

-   Add compatibility for Wagtail 5.2
-   Add support for Django 4.2
-   Remove testing for Wagtail 4.2, 5.0

## [1.8.0] - 2023-11-24

-   Upgrade to allow latest Wagtail versions (4.1+)
-   Drop support for wagtail < 4.1
-   Remove testing for python 3.7

## [1.7.0] - 2023-02-08

### Changed

-   Upgrade the required Braintree SDK version to at least 4.17.1+.

## [1.6.0] - 2022-12-01

### Dev

-   Upgrade to allow latest Wagtail 4.1.1 and latest Django 4.1

### [1.5.0rc2] - 2022-05-14

## Dev

-   Fix Wagtail 3.0 Import error

## [1.5.0rc1] - 2022-05-07

## Dev

-   Fix `get_main_nav_soup` getting the navigation bar from HTML issue, where Wagtail>=2.16 stores it inside a script tag instead.
-   Support Wagtail 3.0

## [1.4.0] - 2022-04-06

## Added

-   Allow override of merchant account id in braintree payment methods via context kwarg

## Dev

-   Update Black to 22.3.0.
-   Set Prettier to ignore `.mypy_cache`

## [1.3.1] - 2021-11-09

### Changed

-   Update deprecated import of `re_path` method for future compatibility.

## [1.3.0] - 2021-07-01

### Added

-   3D Secure verification for Braintree card payments

### Changed

-   Upgrade to version 3.76.4 of the Braintree JS scripts

## [1.2.1] - 2021-06-14

### Changed

-   CI updated to test against Wagtail 2.13 and Django 3.2.
-   CI updated to allow tests against the bleeding-edge version of Wagtail to fail.

### Fixed

-   The 'Payments' menu item will now correctly show for users with (only) the 'Export Pay Ins' permission.
-   The export view now uses local datetimes when filtering by date.
-   CI no longer warns about naive datetimes, or sporadically fails due to datetime issues.

## [1.2.0] - 2021-04-30

### Changed

-   Packages are now released to PyPI under a non-free licence and releases are no longer made to AWS CodeArtifact

### Fixed

-   Duplicated and incorrect information about `PAY_IN_*` settings has been removed from the docs.

## [1.1.2] - 2020-12-21

### Fixed

-   Mistyped configuration property for Google Pay (merchantId -> googleMerchantId) (!98)
-   Fix requesting of email and phone number fields from shipping details and convert country code to upper case when using Apple Pay payment method

## [1.1.1] - 2020-10-12

### Changed

-   Ensure inherited serializer's validate method is called from PayInSerializer

## [1.1.0] - 2020-10-12

### Added

-   Pass parent page context to donation streamfield block
-   Added reCAPTCHA v3 to checkout

### Changed

-   Allow fundraising pay-in event model to be customised
-   Fix name of `gift_aid_declaration` in thank you page context

## [1.0.0] - 2020-08-27

### Added

-   Fundraising pay-in events
-   Publishing package to CodeArtifact
-   Support for decimal donation amounts

### Changed

-   Allow phone number to be plain string rather than PhoneNumber object

### Removed

-   Separate pay-in checkout

[unreleased]: https://git.torchbox.com/internal/wagtail-donate/-/compare/v1.2.0...HEAD
[1.2.0]: https://git.torchbox.com/internal/wagtail-donate/-/compare/v1.1.2...v1.2.0
[1.1.2]: https://git.torchbox.com/internal/wagtail-donate/-/compare/v1.1.1...v1.1.2
[1.1.1]: https://git.torchbox.com/internal/wagtail-donate/-/compare/v1.1.0...v1.1.1
[1.1.0]: https://git.torchbox.com/internal/wagtail-donate/-/compare/v1.0.0...v1.1.0
[1.0.0]: https://git.torchbox.com/internal/wagtail-donate/-/tags/v1.0.0

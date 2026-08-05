# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning is semantic (see [DEVELOPMENT.md](DEVELOPMENT.md)); pre-1.0, anything may break between minor versions. Python and R share one version number.

## [0.1.0] - 2026-08-05

### Added

- `vessel_profile_url()` and `vessel_map_url()`, for Python and R, built from one shared spec (`specs/url_test_cases.json`) so both stay identical.
- Weekly live-app check (`live` workflow) confirming generated URLs still ask the real GFW map API for what they specify.

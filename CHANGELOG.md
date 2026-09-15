# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1] - 2026-09-15

### Added
- **GitHub Actions CI/CD Pipeline:** Added comprehensive multi-step pipeline (`.github/workflows/ci.yml`) featuring Ruff linting, Mypy static type checking, Pytest test runner, and automated PyPI Trusted Publishing on tag pushes (`v*`).

### Fixed
- **Typecheck & Mypy Compatibility:** Fixed `TokenManager.tokens` property, corrected `UserProfile` instantiation keyword arguments in `GoogleHealthProvider`, and updated `params` type annotations in `FitbitClient`.

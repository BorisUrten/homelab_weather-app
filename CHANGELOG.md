# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Health Checks**: Implemented `/health` and `/ready` endpoints for Kubernetes probes.
- **Metrics**: Added Prometheus metrics for API requests, DB operations, and weather data.
- **Graceful Shutdown**: Added signal handling for SIGTERM/SIGINT.
- **Documentation**: Added comprehensive `ARCHITECTURE.md` and `SECURITY.md`.
- **Secrets Example**: Added `secrets.example.yaml` for safe configuration reference.
- **Tests**: Added basic unit test suite.

### Changed
- **Base Image**: Updated Dockerfile to run as non-root user (UID 1000).
- **CI/CD**: Upgraded GitHub Actions to latest major versions (v4/v5).
- **README**: Completely overhauled with architecture diagrams and badge status.

### Fixed
- Fixed typo in README referring to `grafana-db-secret.yamal`.
- Updated package author metadata in `__init__.py`.

## [1.0.0] - 2023-12-10

### Initial Release
- Basic weather polling application.
- PostgreSQL database integration.
- Flux CD GitOps configuration.
- Grafana dashboard setup.

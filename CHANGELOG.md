# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- N/A

### Changed
- N/A

### Fixed
- N/A

## [0.1.1] - 2025-06-16

### Fixed
- Corrected release date in CHANGELOG.md for v0.1.0

## [0.1.0] - 2025-06-16

### Added
- Initial project structure setup
- ProPublica MCP Server implementation plan
- Entity Relationship Diagram for data modeling
- Project documentation (README, requirements, etc.)
- Basic FastMCP server framework integration
- Complete MCP server implementation with 6 tools:
  - `search_nonprofits` - Search for nonprofit organizations
  - `get_organization` - Get detailed organization information
  - `get_organization_filings` - Get Form 990 filings
  - `analyze_nonprofit_financials` - Analyze financial trends
  - `search_similar_nonprofits` - Find similar organizations
  - `export_nonprofit_data` - Export data for CRM integration
- Comprehensive data models with validation
- API client with rate limiting and error handling
- Full test suite with 30+ tests passing
- Docker support with multi-stage builds
- Docker Compose configuration for easy deployment
- GitHub Actions workflow for automated Docker publishing
- GitHub Container Registry integration
- Multi-architecture Docker images (linux/amd64, linux/arm64)
- Security scanning with Trivy
- Docker publishing script for manual deployments
- Proper logging configuration for MCP protocol compatibility

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A 
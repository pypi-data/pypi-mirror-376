# Changelog

All notable changes to the Meridian SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-12

### Added
- Initial release of Meridian SDK for Python
- Core search functionality with AI-powered natural language processing
- Support for multiple data sources (SharePoint, Google Drive)
- Automatic retry logic with exponential backoff
- Rate limiting and usage tracking
- Connector management for data sources
- Comprehensive error handling
- Full async/await support
- Type hints for better IDE support
- Health check and status monitoring endpoints
- Request validation before execution
- Conversation context management
- Usage and billing information endpoints

### Features
- `MeridianAPI` client class with async context manager support
- `search()` method for AI-powered searches
- `get_usage()` for usage statistics and billing
- `get_limits()` for rate limit information
- `health_check()` for system health monitoring
- `get_status()` for API status and features
- `validate_request()` for request validation
- `get_connector_status()` for data source status
- `connect_data_source()` for initiating OAuth flows
- Helper functions for response formatting and client creation

### Documentation
- Comprehensive README with examples
- API documentation with all endpoints
- Usage examples for common scenarios
- Best practices guide

### Security
- Bearer token authentication
- Secure API key management
- No hardcoded credentials
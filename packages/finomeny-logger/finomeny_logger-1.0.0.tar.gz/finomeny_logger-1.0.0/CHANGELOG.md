# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Planning for real-time log streaming
- OpenSearch direct output integration
- Custom PII detection patterns
- Log sampling for high-volume services

## [1.0.0] - 2025-09-11

### Added
- Initial release of Finomeny Logger
- Structured JSON logging with enforced schema
- AWS auto-detection (Lambda, EC2, region, etc.)
- Built-in PII detection and redaction
- JSON Schema validation for log consistency
- Distributed tracing with correlation and trace IDs
- Domain-specific context blocks for:
  - Snowflake operations
  - Salesforce API calls
  - Airflow tasks
  - Step Functions
  - RDS operations
  - File ingestion
- Operation tracing with automatic timing
- Comprehensive error handling and stack trace management
- Support for all log levels (DEBUG, INFO, WARN, ERROR, CRITICAL)
- Log categorization (Security, Compliance, BusinessTransaction, Engagement, TechnicalOps)
- Performance monitoring and metrics collection
- GDPR-compliant logging with automatic data classification
- Pre-commit hooks for code quality
- Comprehensive test suite with 95%+ coverage
- GitHub Actions CI/CD pipeline
- Automatic PyPI publishing on release

### Security
- PII redaction using regex patterns for:
  - Email addresses
  - Phone numbers
  - Social Security Numbers
  - Credit card numbers
  - API tokens and keys
- Sensitive ID hashing for correlation without exposure
- Configurable redaction strategies

### Documentation
- Complete README with usage examples
- API documentation with type hints
- Usage examples for common scenarios:
  - Lambda functions
  - Airflow DAGs
  - API services
  - Payment processing
  - GDPR compliance
  - Multi-system integration
- Development setup guide
- Contributing guidelines

### Dependencies
- boto3>=1.26.0 for AWS integration
- jsonschema>=4.0.0 for log validation
- typing-extensions for Python 3.8 compatibility

## [0.1.0] - 2025-09-01

### Added
- Project structure and initial development setup
- Core logging framework design
- Basic AWS integration planning
# Finomeny Logger

[![PyPI version](https://badge.fury.io/py/finomeny-logger.svg)](https://badge.fury.io/py/finomeny-logger)
[![Python Support](https://img.shields.io/pypi/pyversions/finomeny-logger.svg)](https://pypi.org/project/finomeny-logger/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://codecov.io/gh/finomeny/finomeny-logger/branch/main/graph/badge.svg)](https://codecov.io/gh/finomeny/finomeny-logger)

Production-ready structured logging library for Finomeny services. Provides consistent, JSON-structured logs across AWS services with automatic context detection, PII redaction, and comprehensive observability features.

## 🚀 Features

- **Structured JSON Logging**: Enforces consistent log format across all services
- **AWS Auto-Detection**: Automatically detects Lambda, EC2, and other AWS contexts
- **PII Protection**: Built-in PII detection and redaction with configurable strategies
- **Schema Validation**: JSON Schema validation for log consistency
- **Distributed Tracing**: Correlation IDs and trace IDs for request tracking
- **Domain Contexts**: Pre-built context blocks for Snowflake, Salesforce, Airflow, etc.
- **Performance Monitoring**: Built-in operation tracing with timing metrics
- **Compliance Ready**: GDPR-compliant logging with automatic data classification

## 📦 Installation

```bash
pip install finomeny-logger
```

For development:
```bash
pip install finomeny-logger[dev]
```

## 🏃 Quick Start

### Basic Usage

```python
from finomeny_logger import FinomenyLogger, LogCategory

# Initialize logger (auto-detects AWS context)
logger = FinomenyLogger(
    service="portfolio-api",
    component="lambda", 
    version="1.2.3"
)

# Log business events
logger.info(
    "Portfolio.Created",
    "New portfolio created successfully",
    category=LogCategory.BUSINESS_TRANSACTION,
    portfolio_id="PORT-12345",
    actor_id="user123",
    metrics={"portfolios_created": 1}
)

# Log with error handling
try:
    risky_operation()
except Exception as e:
    logger.error(
        "Portfolio.CreationFailed", 
        "Portfolio creation failed",
        error=e,
        portfolio_id="PORT-12345"
    )
```

### AWS Lambda Function

```python
from finomeny_logger import FinomenyLogger, create_ingestion_context

def lambda_handler(event, context):
    logger = FinomenyLogger(
        service="portfolio-ingester",
        component="lambda",
        version="2.1.4"
    )
    
    portfolio_id = event['portfolio_id']
    
    # Use operation tracing for automatic timing
    with logger.trace_operation(
        "ProcessPortfolio",
        portfolio_id=portfolio_id,
        source_system="s3",
        target_system="snowflake"
    ) as tracer:
        
        # Your processing logic here
        process_portfolio_file(event['s3_key'])
        
        # Log with domain context
        logger.info(
            "Portfolio.Processed",
            f"Portfolio {portfolio_id} processed successfully",
            portfolio_id=portfolio_id,
            metrics={"rows_processed": 10000},
            **create_ingestion_context(
                source_type="xls",
                file_key=event['s3_key']
            )
        )
    
    return {"statusCode": 200}
```

### Airflow Integration

```python
from finomeny_logger import FinomenyLogger, create_airflow_context

def my_airflow_task(**context):
    logger = FinomenyLogger(
        service="data-pipeline",
        component="airflow",
        version="1.0.0"
    )
    
    # Extract Airflow context
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    run_id = context['run_id']
    
    logger.info(
        "ETL.TaskStarted",
        f"Starting ETL task: {task_id}",
        **create_airflow_context(dag_id, task_id, run_id)
    )
    
    # Your ETL logic here
```

## 📊 Structured Log Format

Every log follows this structured format:

```json
{
  "ts": "2025-09-11T09:30:15.123Z",
  "env": "prod",
  "service": "portfolio-ingester", 
  "component": "lambda",
  "version": "2.1.4",
  "region": "eu-west-2",
  "level": "INFO",
  "category": "BusinessTransaction",
  "event": "Portfolio.Processed",
  "message": "Portfolio processing completed",
  "trace_id": "0f8fad5b-d9cb-469f-a165-70867728950e",
  "correlation_id": "req-8d3e1c1b9f",
  "portfolio_id": "PORT-12345",
  "actor_id": "user123",
  "pii_flags": ["none"],
  "metrics": {
    "rows_processed": 10000,
    "latency_ms": 1250
  },
  "tags": ["portfolio", "processing"],
  "kvs": {
    "file_key": "data/portfolio.xlsx"
  }
}
```

### Required Fields

- `ts`: ISO 8601 timestamp
- `env`: Environment (dev/stg/prod) 
- `service`: Service name
- `component`: Component type (lambda/api/airflow/etc)
- `version`: Service version
- `region`: AWS region
- `level`: Log level (DEBUG/INFO/WARN/ERROR/CRITICAL)
- `category`: Event category (Security/Compliance/BusinessTransaction/Engagement/TechnicalOps)
- `event`: Event name (PascalCase with dots)
- `message`: Human-readable message
- `pii_flags`: PII classification
- `metrics`: Quantitative data
- `kvs`: Additional key-value pairs

## 🔐 PII Protection

The logger automatically detects and redacts PII:

```python
# Automatic PII redaction
logger.info(
    "User.ContactUpdated",
    "User updated contact: john.doe@example.com and +1-555-123-4567",
    # Output: "User updated contact: [REDACTED_EMAIL] and [REDACTED_PHONE]"
    pii_flags=["contains-pii"]
)

# Sensitive ID hashing
logger.info(
    "Payment.Processed", 
    "Payment processed for debtor",
    debtor_id="DEBT-12345"  # Automatically hashed to protect PII
)
```

## 📋 Domain Contexts

Use pre-built context blocks for common integrations:

### Snowflake Context

```python
from finomeny_logger import create_snowflake_context

logger.info(
    "Transform.Complete",
    "Data transformation finished",
    **create_snowflake_context(
        query_id="01a12345-0400-5db1-0000-0f5c00a1bdf6",
        rows_affected=10000,
        credit_cost_est=0.05
    )
)
```

### Salesforce Context

```python
logger.info(
    "Salesforce.UpsertComplete",
    "Records upserted to Salesforce",
    salesforce_ctx={
        "api": "Bulk",
        "object": "Debt__c", 
        "operation": "upsert",
        "batch_id": "751xxxxxxxxxxxx",
        "success_count": 9950,
        "error_count": 50
    }
)
```

### Ingestion Context

```python
from finomeny_logger import create_ingestion_context

logger.info(
    "File.Processed",
    "File ingestion completed", 
    **create_ingestion_context(
        source_type="csv",
        file_key="data/import.csv",
        checksum="sha256:abc123",
        headers_detected=True
    )
)
```

## 🎯 Log Categories & Levels

### Categories

- `Security`: Authentication, authorization, access control
- `Compliance`: GDPR, audit trails, regulatory events  
- `BusinessTransaction`: Core business operations
- `Engagement`: User interactions, communications
- `TechnicalOps`: Infrastructure, performance, errors

### Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational messages
- `WARN`: Warning conditions that should be addressed
- `ERROR`: Error conditions that don't stop operation
- `CRITICAL`: Critical errors requiring immediate attention

## ⚡ Performance Monitoring

Built-in operation tracing with automatic timing:

```python
# Automatic timing and error handling
with logger.trace_operation(
    "DatabaseQuery", 
    portfolio_id="PORT-123",
    metrics={"query_complexity": "high"}
) as tracer:
    
    # Your operation here
    result = execute_complex_query()
    
    # Timing automatically added to metrics
    # Errors automatically logged if exception occurs
```

## 🔧 Configuration

### Environment Variables

The logger auto-detects configuration from environment:

- `ENVIRONMENT` / `ENV` / `STAGE`: Environment name
- `AWS_REGION`: AWS region
- `AWS_LAMBDA_FUNCTION_NAME`: Lambda function name
- `_X_AMZN_TRACE_ID`: AWS request tracing

### Initialization Options

```python
logger = FinomenyLogger(
    service="my-service",
    component="lambda",
    version="1.0.0",
    env="prod",                    # Override auto-detection
    region="us-east-1",           # Override auto-detection  
    auto_detect_aws=True,         # Enable AWS context detection
    validate_schema=True,         # Enable JSON schema validation
    redact_pii=True,             # Enable PII redaction
    max_error_stack_size=8192    # Limit error stack size
)
```

## 📈 AWS Integration

### CloudWatch Logs

Logs automatically flow to CloudWatch when running in Lambda:

```python
# In Lambda, logs go directly to CloudWatch
logger.info("Lambda.Started", "Function execution started")
```

### S3 Data Lake

Configure EventBridge rules to route logs to S3:

```
Pattern: s3://logs/{env}/{service}/dt=YYYY-MM-DD/region={region}/
```

### OpenSearch Indexing

Recommended index pattern:

```
Index: {env}-{service}-yyyy.mm.dd
Partition: (env, service, date(ts))
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=finomeny_logger

# Run specific test types
pytest tests/unit
pytest tests/integration
```

## 📚 Advanced Usage

### Custom Context Blocks

```python
# Create custom domain context
def create_payment_context(payment_id, amount, currency):
    return {
        "payment_ctx": {
            "payment_id": payment_id,
            "amount": amount, 
            "currency": currency,
            "processor": "stripe"
        }
    }

logger.info(
    "Payment.Processed",
    "Payment completed",
    **create_payment_context("PAY-123", 100.00, "USD")
)
```

### Correlation Across Services

```python
# Service A
logger.info(
    "Request.Started", 
    "Processing user request",
    correlation_id="req-abc123"
)

# Service B (use same correlation_id)
logger.info(
    "Data.Fetched",
    "Retrieved user data", 
    correlation_id="req-abc123"  # Same ID for tracing
)
```

### GDPR Compliance

```python
# Automatically classify and protect PII
logger.info(
    "User.DataProcessed",
    "User personal data processed",
    debtor_id="DEBT-123",      # Automatically hashed
    pii_flags=["tokenized"],   # Explicit PII classification
    kvs={
        "processing_purpose": "debt_collection",
        "legal_basis": "contract",
        "retention_period_days": 2555
    }
)
```

## 🏗️ Development

### Setup Development Environment

```bash
git clone https://github.com/FinomenyTech/finomeny-logger.git
cd finomeny-logger
pip install -e ".[dev]"
pre-commit install
```

### Code Quality

```bash
# Format code
black src tests

# Sort imports  
isort src tests

# Lint
flake8 src tests

# Type check
mypy src
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- 📧 Email: nesi@finomeny.es
- 🐛 Issues: [GitHub Issues](https://github.com/FinomenyTech/finomeny-logger/issues)
- 📚 Documentation: [Read the Docs](https://finomeny-logger.readthedocs.io)

## 🚀 Roadmap

- [ ] Elasticsearch/OpenSearch direct output
- [ ] Metrics collection integration (Prometheus)
- [ ] Custom PII detection patterns
- [ ] Log sampling for high-volume services
- [ ] Real-time log streaming
- [ ] Integration with AWS X-Ray

---

**Made with ❤️ by the Finomeny Engineering Team**
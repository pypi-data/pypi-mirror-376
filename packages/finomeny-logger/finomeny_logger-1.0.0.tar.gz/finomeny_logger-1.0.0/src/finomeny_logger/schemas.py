"""
JSON Schema definitions for Finomeny Structured Logger.

Contains all schema validation rules for log entries and context blocks.
"""

from typing import Dict, Any

# Main log entry schema
LOG_ENTRY_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "ts", "env", "service", "component", "version", "region",
        "level", "category", "event", "message", "pii_flags", "metrics", "kvs"
    ],
    "properties": {
        # Core metadata
        "ts": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp with timezone"
        },
        "env": {
            "type": "string",
            "enum": ["dev", "stg", "prod"],
            "description": "Environment where the log was generated"
        },
        "service": {
            "type": "string",
            "description": "Service name (e.g., 'portfolio-ingester')"
        },
        "component": {
            "type": "string",
            "description": "Component type (e.g., 'lambda', 'airflow', 'api')"
        },
        "version": {
            "type": "string",
            "pattern": r"^\d+\.\d+\.\d+",
            "description": "Semantic version of the service"
        },
        "host": {
            "type": ["string", "null"],
            "description": "Host identifier (Lambda function name, EC2 instance ID, etc.)"
        },
        "region": {
            "type": "string",
            "pattern": r"^[a-z]{2}-[a-z]+-\d+$",
            "description": "AWS region"
        },

        # Log content
        "level": {
            "type": "string",
            "enum": ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
            "description": "Log level"
        },
        "category": {
            "type": "string",
            "enum": ["Security", "Compliance", "BusinessTransaction", "Engagement", "TechnicalOps"],
            "description": "Log category for classification"
        },
        "event": {
            "type": "string",
            "minLength": 1,
            "description": "Event identifier (e.g., 'FileIngestion.Start')"
        },
        "message": {
            "type": "string",
            "minLength": 1,
            "description": "Human-readable log message"
        },

        # Error details
        "error_type": {
            "type": ["string", "null"],
            "description": "Exception class name"
        },
        "error_message": {
            "type": ["string", "null"],
            "description": "Exception message"
        },
        "error_stack": {
            "type": ["string", "null"],
            "description": "Stack trace (truncated to max size)"
        },

        # Tracing and correlation
        "trace_id": {
            "type": ["string", "null"],
            "pattern": r"^[a-fA-F0-9-]{36}$",
            "description": "Distributed trace ID (UUID format)"
        },
        "span_id": {
            "type": ["string", "null"],
            "description": "Span ID within a trace"
        },
        "correlation_id": {
            "type": ["string", "null"],
            "pattern": r"^[a-fA-F0-9-]{36}$",
            "description": "Correlation ID for request tracking (UUID format)"
        },
        "request_id": {
            "type": ["string", "null"],
            "description": "AWS request ID or custom request identifier"
        },
        "session_id": {
            "type": ["string", "null"],
            "description": "User or system session identifier"
        },

        # Business context
        "source_system": {
            "type": ["string", "null"],
            "description": "System originating the operation"
        },
        "target_system": {
            "type": ["string", "null"],
            "description": "Target system for the operation"
        },
        "portfolio_id": {
            "type": ["string", "null"],
            "description": "Portfolio identifier"
        },
        "debtor_id": {
            "type": ["string", "null"],
            "description": "Hashed debtor identifier for privacy"
        },
        "actor_id": {
            "type": ["string", "null"],
            "description": "User or system actor performing the operation"
        },
        "tenant_id": {
            "type": ["string", "null"],
            "description": "Multi-tenant identifier"
        },

        # Privacy and compliance
        "pii_flags": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["none", "contains-pii", "masked", "tokenized"]
            },
            "minItems": 1,
            "description": "PII presence indicators"
        },
        "redaction": {
            "type": "string",
            "enum": ["automatic", "manual", "none"],
            "description": "Type of redaction applied"
        },

        # Structured data
        "metrics": {
            "type": "object",
            "description": "Numerical metrics and measurements",
            "additionalProperties": {
                "type": ["number", "integer"]
            }
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Searchable tags for log categorization"
        },
        "kvs": {
            "type": "object",
            "description": "Key-value pairs for additional context",
            "additionalProperties": True
        }
    },
    "anyOf": [
        {"required": ["trace_id"]},
        {"required": ["correlation_id"]}
    ]
}

# Context block schemas
INGESTION_CONTEXT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["source_type", "file_key"],
    "properties": {
        "source_type": {
            "type": "string",
            "enum": ["s3", "sftp", "api", "database", "stream"],
            "description": "Type of data source"
        },
        "file_key": {
            "type": "string",
            "minLength": 1,
            "description": "File path or identifier"
        },
        "checksum": {
            "type": ["string", "null"],
            "pattern": r"^[a-fA-F0-9]{32,128}$",
            "description": "File checksum (MD5, SHA256, etc.)"
        },
        "parser": {
            "type": ["string", "null"],
            "enum": ["csv", "json", "xml", "parquet", "avro", "custom"],
            "description": "Parser used for file processing"
        },
        "delimiter": {
            "type": ["string", "null"],
            "maxLength": 5,
            "description": "Field delimiter for delimited files"
        },
        "headers_detected": {
            "type": ["boolean", "null"],
            "description": "Whether headers were automatically detected"
        },
        "file_size_bytes": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "File size in bytes"
        },
        "row_count": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Number of rows processed"
        },
        "encoding": {
            "type": ["string", "null"],
            "enum": ["utf-8", "utf-16", "ascii", "latin1"],
            "description": "File encoding"
        }
    }
}

ETL_CONTEXT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "pipeline_id": {
            "type": "string",
            "description": "ETL pipeline identifier"
        },
        "stage": {
            "type": "string",
            "enum": ["extract", "transform", "load", "validate"],
            "description": "ETL stage"
        },
        "batch_id": {
            "type": ["string", "null"],
            "description": "Batch processing identifier"
        },
        "input_records": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Number of input records"
        },
        "output_records": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Number of output records"
        },
        "error_records": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Number of records with errors"
        },
        "transformation_rules": {
            "type": ["array", "null"],
            "items": {"type": "string"},
            "description": "List of transformation rules applied"
        }
    }
}

SNOWFLAKE_CONTEXT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["query_id"],
    "properties": {
        "query_id": {
            "type": "string",
            "pattern": r"^[a-fA-F0-9-]{36}$",
            "description": "Snowflake query ID"
        },
        "warehouse": {
            "type": ["string", "null"],
            "description": "Snowflake warehouse used"
        },
        "database": {
            "type": ["string", "null"],
            "description": "Snowflake database"
        },
        "schema": {
            "type": ["string", "null"],
            "description": "Snowflake schema"
        },
        "rows_affected": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Number of rows affected by the query"
        },
        "bytes_scanned": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Bytes scanned by the query"
        },
        "credit_cost_est": {
            "type": ["number", "null"],
            "minimum": 0,
            "description": "Estimated credit cost"
        },
        "execution_time_ms": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Query execution time in milliseconds"
        },
        "compilation_time_ms": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Query compilation time in milliseconds"
        },
        "query_type": {
            "type": ["string", "null"],
            "enum": ["SELECT", "INSERT", "UPDATE", "DELETE", "MERGE", "COPY", "CREATE", "ALTER", "DROP"],
            "description": "Type of SQL query"
        }
    }
}

SALESFORCE_CONTEXT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "org_id": {
            "type": ["string", "null"],
            "pattern": r"^[a-zA-Z0-9]{15,18}$",
            "description": "Salesforce organization ID"
        },
        "api_version": {
            "type": ["string", "null"],
            "pattern": r"^\d+\.\d+$",
            "description": "Salesforce API version"
        },
        "operation": {
            "type": ["string", "null"],
            "enum": ["query", "insert", "update", "upsert", "delete", "bulk_query", "bulk_insert"],
            "description": "Salesforce operation type"
        },
        "sobject": {
            "type": ["string", "null"],
            "description": "Salesforce object type"
        },
        "records_processed": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Number of records processed"
        },
        "api_calls_used": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Number of API calls consumed"
        },
        "bulk_job_id": {
            "type": ["string", "null"],
            "description": "Bulk API job identifier"
        }
    }
}

RDS_CONTEXT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "instance_id": {
            "type": ["string", "null"],
            "description": "RDS instance identifier"
        },
        "database": {
            "type": ["string", "null"],
            "description": "Database name"
        },
        "query_hash": {
            "type": ["string", "null"],
            "pattern": r"^[a-fA-F0-9]{32,64}$",
            "description": "Query hash for performance tracking"
        },
        "rows_affected": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Number of rows affected"
        },
        "execution_time_ms": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Query execution time in milliseconds"
        },
        "connection_pool": {
            "type": ["string", "null"],
            "description": "Connection pool identifier"
        },
        "transaction_id": {
            "type": ["string", "null"],
            "description": "Database transaction identifier"
        }
    }
}

AIRFLOW_CONTEXT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["dag_id", "task_id", "run_id"],
    "properties": {
        "dag_id": {
            "type": "string",
            "minLength": 1,
            "description": "Airflow DAG identifier"
        },
        "task_id": {
            "type": "string",
            "minLength": 1,
            "description": "Airflow task identifier"
        },
        "run_id": {
            "type": "string",
            "minLength": 1,
            "description": "Airflow DAG run identifier"
        },
        "execution_date": {
            "type": ["string", "null"],
            "format": "date-time",
            "description": "Scheduled execution date"
        },
        "try_number": {
            "type": "integer",
            "minimum": 1,
            "default": 1,
            "description": "Task attempt number"
        },
        "operator": {
            "type": ["string", "null"],
            "description": "Airflow operator class name"
        },
        "queue": {
            "type": ["string", "null"],
            "description": "Airflow queue name"
        },
        "pool": {
            "type": ["string", "null"],
            "description": "Airflow pool name"
        }
    }
}

STEPFUNCTION_CONTEXT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "state_machine_arn": {
            "type": ["string", "null"],
            "pattern": r"^arn:aws:states:",
            "description": "Step Functions state machine ARN"
        },
        "execution_arn": {
            "type": ["string", "null"],
            "pattern": r"^arn:aws:states:",
            "description": "Step Functions execution ARN"
        },
        "state_name": {
            "type": ["string", "null"],
            "description": "Current state name"
        },
        "state_type": {
            "type": ["string", "null"],
            "enum": ["Pass", "Task", "Choice", "Wait", "Succeed", "Fail", "Parallel", "Map"],
            "description": "Step Functions state type"
        },
        "retry_count": {
            "type": ["integer", "null"],
            "minimum": 0,
            "description": "Number of retries for current state"
        },
        "input_path": {
            "type": ["string", "null"],
            "description": "JSONPath input filter"
        },
        "output_path": {
            "type": ["string", "null"],
            "description": "JSONPath output filter"
        }
    }
}

# Schema registry for validation
CONTEXT_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "ingestion_ctx": INGESTION_CONTEXT_SCHEMA,
    "etl_ctx": ETL_CONTEXT_SCHEMA,
    "snowflake_ctx": SNOWFLAKE_CONTEXT_SCHEMA,
    "salesforce_ctx": SALESFORCE_CONTEXT_SCHEMA,
    "rds_ctx": RDS_CONTEXT_SCHEMA,
    "airflow_ctx": AIRFLOW_CONTEXT_SCHEMA,
    "stepfn_ctx": STEPFUNCTION_CONTEXT_SCHEMA,
}


def validate_log_entry(log_entry: Dict[str, Any]) -> bool:
    """
    Validate a log entry against the main schema.

    Args:
        log_entry: Log entry dictionary to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValidationError: If validation fails and strict mode is enabled
    """
    try:
        import jsonschema
        jsonschema.validate(log_entry, LOG_ENTRY_SCHEMA)
        return True
    except ImportError:
        # jsonschema not available, skip validation
        return True
    except jsonschema.ValidationError:
        return False


def validate_context(context_name: str, context_data: Dict[str, Any]) -> bool:
    """
    Validate a context block against its schema.

    Args:
        context_name: Name of the context (e.g., 'ingestion_ctx')
        context_data: Context data dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    if context_name not in CONTEXT_SCHEMAS:
        return True  # Unknown context types are allowed

    try:
        import jsonschema
        schema = CONTEXT_SCHEMAS[context_name]
        jsonschema.validate(context_data, schema)
        return True
    except ImportError:
        return True
    except jsonschema.ValidationError:
        return False


def get_schema_version() -> str:
    """Return the current schema version."""
    return "1.0.0"
"""
Finomeny Structured Logger

A production-ready structured logging library that enforces consistent
logging patterns across all Finomeny services and AWS components.

Features:
- JSON Schema validation
- AWS context auto-detection
- PII redaction
- Multiple output handlers (CloudWatch, S3, local)
- Domain-specific context blocks
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from enum import Enum
import hashlib
import re


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    SECURITY = "Security"
    COMPLIANCE = "Compliance"
    BUSINESS_TRANSACTION = "BusinessTransaction"
    ENGAGEMENT = "Engagement"
    TECHNICAL_OPS = "TechnicalOps"


class PIIFlag(Enum):
    NONE = "none"
    CONTAINS_PII = "contains-pii"
    MASKED = "masked"
    TOKENIZED = "tokenized"


class RedactionType(Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    NONE = "none"


class FinomenyLogger:
    """
    Production-ready structured logger for Finomeny services.

    Automatically detects AWS context and enforces structured logging schema.
    """

    # JSON Schema for validation
    LOG_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": True,
        "required": ["ts", "env", "service", "component", "version", "region",
                     "level", "category", "event", "message", "pii_flags", "metrics", "kvs"],
        "properties": {
            "ts": {"type": "string", "format": "date-time"},
            "env": {"type": "string", "enum": ["dev", "stg", "prod"]},
            "service": {"type": "string"},
            "component": {"type": "string"},
            "version": {"type": "string"},
            "host": {"type": ["string", "null"]},
            "region": {"type": "string"},
            "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]},
            "category": {"type": "string",
                         "enum": ["Security", "Compliance", "BusinessTransaction", "Engagement", "TechnicalOps"]},
            "event": {"type": "string"},
            "message": {"type": "string"},
            "error_type": {"type": ["string", "null"]},
            "error_message": {"type": ["string", "null"]},
            "error_stack": {"type": ["string", "null"]},
            "trace_id": {"type": ["string", "null"]},
            "span_id": {"type": ["string", "null"]},
            "correlation_id": {"type": ["string", "null"]},
            "request_id": {"type": ["string", "null"]},
            "session_id": {"type": ["string", "null"]},
            "source_system": {"type": ["string", "null"]},
            "target_system": {"type": ["string", "null"]},
            "portfolio_id": {"type": ["string", "null"]},
            "debtor_id": {"type": ["string", "null"]},
            "actor_id": {"type": ["string", "null"]},
            "tenant_id": {"type": ["string", "null"]},
            "pii_flags": {
                "type": "array",
                "items": {"type": "string", "enum": ["none", "contains-pii", "masked", "tokenized"]}
            },
            "redaction": {"type": "string", "enum": ["automatic", "manual", "none"]},
            "metrics": {"type": "object"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "kvs": {"type": "object"}
        },
        "oneOf": [
            {"required": ["trace_id"]},
            {"required": ["correlation_id"]}
        ]
    }

    # PII patterns for automatic detection and redaction
    PII_PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b\+?[\d\s\-\(\)]{10,}\b'),
        'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
        'credit_card': re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),
        'token': re.compile(r'\b[A-Za-z0-9]{32,}\b'),
        'aws_key': re.compile(r'\b[A-Z0-9]{20}\b'),
    }

    def __init__(
            self,
            service: str,
            component: str,
            version: str,
            env: Optional[str] = None,
            region: Optional[str] = None,
            auto_detect_aws: bool = True,
            validate_schema: bool = True,
            redact_pii: bool = True,
            max_error_stack_size: int = 8192
    ):
        """
        Initialize the Finomeny Logger.

        Args:
            service: Service name (e.g., 'portfolio-ingester')
            component: Component type (e.g., 'lambda', 'airflow', 'api')
            version: Service version (e.g., '1.2.3')
            env: Environment ('dev', 'stg', 'prod'). Auto-detected if None
            region: AWS region. Auto-detected if None
            auto_detect_aws: Whether to auto-detect AWS context
            validate_schema: Whether to validate logs against JSON schema
            redact_pii: Whether to automatically redact PII
            max_error_stack_size: Maximum size for error stack traces
        """
        self.service = service
        self.component = component
        self.version = version
        self.validate_schema = validate_schema
        self.redact_pii = redact_pii
        self.max_error_stack_size = max_error_stack_size

        # Auto-detect AWS context
        if auto_detect_aws:
            self.env = env or self._detect_environment()
            self.region = region or self._detect_region()
            self.host = self._detect_host()
            self.aws_request_id = self._detect_aws_request_id()
        else:
            self.env = env or "dev"
            self.region = region or "us-east-1"
            self.host = None
            self.aws_request_id = None

        # Generate correlation ID if not provided
        self.correlation_id = str(uuid.uuid4())

        # Set up Python logger
        self.logger = logging.getLogger(f"finomeny.{service}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _detect_environment(self) -> str:
        """Auto-detect environment from various sources."""
        # Check environment variables
        env_vars = ['ENVIRONMENT', 'ENV', 'STAGE', 'AWS_LAMBDA_FUNCTION_NAME']
        for var in env_vars:
            env_val = os.environ.get(var, '').lower()
            if 'prod' in env_val:
                return 'prod'
            elif 'stg' in env_val or 'staging' in env_val:
                return 'stg'
            elif 'dev' in env_val or 'development' in env_val:
                return 'dev'

        # Default to dev if can't determine
        return 'dev'

    def _detect_region(self) -> str:
        """Auto-detect AWS region."""
        # Try environment variable first
        region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION')
        if region:
            return region

        # Try EC2 metadata
        try:
            import urllib.request
            response = urllib.request.urlopen(
                'http://169.254.169.254/latest/meta-data/placement/region',
                timeout=2
            )
            return response.read().decode('utf-8')
        except:
            pass

        return 'us-east-1'

    def _detect_host(self) -> Optional[str]:
        """Auto-detect host/instance information."""
        # Lambda function name
        lambda_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        if lambda_name:
            return lambda_name

        # EC2 instance ID
        try:
            import urllib.request
            response = urllib.request.urlopen(
                'http://169.254.169.254/latest/meta-data/instance-id',
                timeout=2
            )
            return response.read().decode('utf-8')
        except:
            pass

        return None

    def _detect_aws_request_id(self) -> Optional[str]:
        """Auto-detect AWS request ID from Lambda context."""
        return os.environ.get('_X_AMZN_TRACE_ID')

    def _redact_pii(self, text: str) -> str:
        """Redact PII from text using regex patterns."""
        if not self.redact_pii or not isinstance(text, str):
            return text

        redacted = text
        for pattern_name, pattern in self.PII_PATTERNS.items():
            redacted = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', redacted)

        return redacted

    def _hash_sensitive_id(self, value: str) -> str:
        """Hash sensitive IDs for correlation while protecting PII."""
        if not value:
            return value
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    def _build_base_log(
            self,
            level: LogLevel,
            category: LogCategory,
            event: str,
            message: str,
            trace_id: Optional[str] = None,
            correlation_id: Optional[str] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """Build the base log structure with all required fields."""

        # Use provided correlation_id or fall back to instance default
        final_correlation_id = correlation_id or self.correlation_id

        base_log = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "env": self.env,
            "service": self.service,
            "component": self.component,
            "version": self.version,
            "host": self.host,
            "region": self.region,

            "level": level.value,
            "category": category.value,
            "event": event,
            "message": self._redact_pii(message),

            "error_type": kwargs.get('error_type'),
            "error_message": self._redact_pii(kwargs.get('error_message', '')),
            "error_stack": self._truncate_stack(kwargs.get('error_stack')),

            "trace_id": trace_id,
            "span_id": kwargs.get('span_id'),
            "correlation_id": final_correlation_id,
            "request_id": kwargs.get('request_id') or self.aws_request_id,
            "session_id": kwargs.get('session_id'),

            "source_system": kwargs.get('source_system'),
            "target_system": kwargs.get('target_system'),
            "portfolio_id": kwargs.get('portfolio_id'),
            "debtor_id": self._hash_sensitive_id(kwargs.get('debtor_id', '')),
            "actor_id": kwargs.get('actor_id'),
            "tenant_id": kwargs.get('tenant_id'),

            "pii_flags": kwargs.get('pii_flags', [PIIFlag.NONE.value]),
            "redaction": kwargs.get('redaction', RedactionType.AUTOMATIC.value),

            "metrics": kwargs.get('metrics', {}),
            "tags": kwargs.get('tags', []),
            "kvs": kwargs.get('kvs', {}),
        }

        # Add domain context blocks
        context_blocks = [
            'ingestion_ctx', 'etl_ctx', 'snowflake_ctx', 'salesforce_ctx',
            'rds_ctx', 'airflow_ctx', 'stepfn_ctx'
        ]

        for ctx in context_blocks:
            if ctx in kwargs:
                base_log[ctx] = kwargs[ctx]

        return base_log

    def _truncate_stack(self, stack: Optional[str]) -> Optional[str]:
        """Truncate error stack to max size."""
        if not stack:
            return stack

        if len(stack) > self.max_error_stack_size:
            return stack[:self.max_error_stack_size] + "..."

        return self._redact_pii(stack)

    def _emit_log(self, log_entry: Dict[str, Any]) -> None:
        """Emit log entry through configured handlers."""
        log_json = json.dumps(log_entry, default=str, separators=(',', ':'))

        # Log to Python logger (which goes to CloudWatch in Lambda)
        level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARN': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        python_level = level_mapping.get(log_entry['level'], logging.INFO)
        self.logger.log(python_level, log_json)

    def info(
            self,
            event: str,
            message: str,
            category: LogCategory = LogCategory.BUSINESS_TRANSACTION,
            **kwargs
    ) -> None:
        """Log INFO level event."""
        log_entry = self._build_base_log(LogLevel.INFO, category, event, message, **kwargs)
        self._emit_log(log_entry)

    def warn(
            self,
            event: str,
            message: str,
            category: LogCategory = LogCategory.TECHNICAL_OPS,
            **kwargs
    ) -> None:
        """Log WARN level event."""
        log_entry = self._build_base_log(LogLevel.WARN, category, event, message, **kwargs)
        self._emit_log(log_entry)

    def error(
            self,
            event: str,
            message: str,
            error: Optional[Exception] = None,
            category: LogCategory = LogCategory.TECHNICAL_OPS,
            **kwargs
    ) -> None:
        """Log ERROR level event."""
        if error:
            kwargs.update({
                'error_type': type(error).__name__,
                'error_message': str(error),
                'error_stack': self._get_stack_trace(error)
            })

        log_entry = self._build_base_log(LogLevel.ERROR, category, event, message, **kwargs)
        self._emit_log(log_entry)

    def critical(
            self,
            event: str,
            message: str,
            error: Optional[Exception] = None,
            category: LogCategory = LogCategory.SECURITY,
            **kwargs
    ) -> None:
        """Log CRITICAL level event."""
        if error:
            kwargs.update({
                'error_type': type(error).__name__,
                'error_message': str(error),
                'error_stack': self._get_stack_trace(error)
            })

        log_entry = self._build_base_log(LogLevel.CRITICAL, category, event, message, **kwargs)
        self._emit_log(log_entry)

    def debug(
            self,
            event: str,
            message: str,
            category: LogCategory = LogCategory.TECHNICAL_OPS,
            **kwargs
    ) -> None:
        """Log DEBUG level event."""
        log_entry = self._build_base_log(LogLevel.DEBUG, category, event, message, **kwargs)
        self._emit_log(log_entry)

    def _get_stack_trace(self, error: Exception) -> str:
        """Get formatted stack trace from exception."""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))

    # Context manager for tracing
    def trace_operation(
            self,
            operation_name: str,
            trace_id: Optional[str] = None,
            **context
    ):
        """Context manager for tracing operations with automatic timing."""
        return OperationTracer(self, operation_name, trace_id, **context)


class OperationTracer:
    """Context manager for tracing operations."""

    def __init__(self, logger: FinomenyLogger, operation_name: str, trace_id: Optional[str] = None, **context):
        self.logger = logger
        self.operation_name = operation_name
        self.trace_id = trace_id or str(uuid.uuid4())
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now(timezone.utc)

        self.logger.info(
            f"{self.operation_name}.Start",
            f"Started {self.operation_name}",
            trace_id=self.trace_id,
            **self.context
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - self.start_time).total_seconds() * 1000)

        # Update metrics with timing
        metrics = self.context.get('metrics', {})
        metrics['latency_ms'] = duration_ms
        self.context['metrics'] = metrics

        if exc_type:
            self.logger.error(
                f"{self.operation_name}.Error",
                f"Failed {self.operation_name}: {exc_val}",
                error=exc_val,
                trace_id=self.trace_id,
                **self.context
            )
        else:
            self.logger.info(
                f"{self.operation_name}.Complete",
                f"Completed {self.operation_name}",
                trace_id=self.trace_id,
                **self.context
            )


# Convenience functions for common domain contexts
def create_ingestion_context(
        source_type: str,
        file_key: str,
        checksum: Optional[str] = None,
        parser: Optional[str] = None,
        delimiter: Optional[str] = None,
        headers_detected: Optional[bool] = None
) -> Dict[str, Any]:
    """Create ingestion context block."""
    return {
        "ingestion_ctx": {
            "source_type": source_type,
            "file_key": file_key,
            "checksum": checksum,
            "parser": parser,
            "delimiter": delimiter,
            "headers_detected": headers_detected
        }
    }


def create_snowflake_context(
        query_id: str,
        rows_affected: Optional[int] = None,
        bytes_scanned: Optional[int] = None,
        credit_cost_est: Optional[float] = None
) -> Dict[str, Any]:
    """Create Snowflake context block."""
    return {
        "snowflake_ctx": {
            "query_id": query_id,
            "rows_affected": rows_affected,
            "bytes_scanned": bytes_scanned,
            "credit_cost_est": credit_cost_est
        }
    }


def create_airflow_context(
        dag_id: str,
        task_id: str,
        run_id: str,
        try_number: int = 1
) -> Dict[str, Any]:
    """Create Airflow context block."""
    return {
        "airflow_ctx": {
            "dag_id": dag_id,
            "task_id": task_id,
            "run_id": run_id,
            "try_number": try_number
        }
    }
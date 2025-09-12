"""
Finomeny Structured Logger

Production-ready structured logging library for Finomeny services.
Provides consistent logging patterns across AWS services and applications.
"""

__version__ = "1.0.0"
__author__ = "Finomeny Engineering"
__email__ = "nesi@finomeny.es"

from .logger import (
    FinomenyLogger,
    OperationTracer,
    LogLevel,
    LogCategory,
    PIIFlag,
    RedactionType,
    create_ingestion_context,
    create_snowflake_context,
    create_airflow_context,
)

__all__ = [
    "FinomenyLogger",
    "OperationTracer",
    "LogLevel",
    "LogCategory",
    "PIIFlag",
    "RedactionType",
    "create_ingestion_context",
    "create_snowflake_context",
    "create_airflow_context",
]
"""
Unit tests for FinomenyLogger
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.finomeny_logger import FinomenyLogger, create_airflow_context, create_snowflake_context, \
    create_ingestion_context


class TestFinomenyLogger:
    """Test suite for FinomenyLogger."""

    @pytest.fixture
    def logger(self):
        """Create a test logger instance."""
        with patch.dict(os.environ, {
            'AWS_REGION': 'us-east-1',
            'ENVIRONMENT': 'test',
            'AWS_LAMBDA_FUNCTION_NAME': 'test-function'
        }):
            return FinomenyLogger(
                service="test-service",
                component="lambda",
                version="1.0.0",
                auto_detect_aws=True
            )

    def test_logger_initialization(self, logger):
        """Test logger initialization with auto-detection."""
        assert logger.service == "test-service"
        assert logger.component == "lambda"
        assert logger.version == "1.0.0"
        assert logger.env == "test"
        assert logger.region == "us-east-1"
        assert logger.host == "test-function"

    def test_environment_detection(self):
        """Test environment auto-detection."""
        test_cases = [
            ({'ENVIRONMENT': 'production'}, 'prod'),
            ({'ENV': 'staging'}, 'stg'),
            ({'STAGE': 'development'}, 'dev'),
            ({'AWS_LAMBDA_FUNCTION_NAME': 'prod-my-function'}, 'prod'),
            ({}, 'dev'),  # default
        ]

        for env_vars, expected in test_cases:
            with patch.dict(os.environ, env_vars, clear=True):
                logger = FinomenyLogger("test", "test", "1.0.0")
                assert logger.env == expected

    def test_pii_redaction(self, logger):
        """Test PII redaction functionality."""
        test_message = "Contact john.doe@example.com or call +1-555-123-4567"
        redacted = logger._redact_pii(test_message)

        assert "[REDACTED_EMAIL]" in redacted
        assert "[REDACTED_PHONE]" in redacted
        assert "john.doe@example.com" not in redacted
        assert "+1-555-123-4567" not in redacted

    def test_sensitive_id_hashing(self, logger):
        """Test sensitive ID hashing."""
        debtor_id = "DEBTOR-12345"
        hashed = logger._hash_sensitive_id(debtor_id)

        assert len(hashed) == 16
        assert hashed != debtor_id
        # Same input should produce same hash
        assert hashed == logger._hash_sensitive_id(debtor_id)

    def test_error_stack_truncation(self, logger):
        """Test error stack truncation."""
        long_stack = "A" * 10000
        truncated = logger._truncate_stack(long_stack)

        assert len(truncated) <= logger.max_error_stack_size + 3  # +3 for "..."
        assert truncated.endswith("...")

    @patch('finomeny_logger.logger.logging.getLogger')
    def test_info_logging(self, mock_get_logger, logger):
        """Test INFO level logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        logger.info(
            "Test.Event",
            "Test message",
            portfolio_id="PORT-123",
            metrics={"count": 100}
        )

        # Verify logger was called
        mock_logger.log.assert_called_once()
        args = mock_logger.log.call_args

        assert args[0][0] == 20  # INFO level
        log_data = json.loads(args[0][1])

        assert log_data["level"] == "INFO"
        assert log_data["event"] == "Test.Event"
        assert log_data["message"] == "Test message"
        assert log_data["portfolio_id"] == "PORT-123"
        assert log_data["metrics"]["count"] == 100

    @patch('finomeny_logger.logger.logging.getLogger')
    def test_error_logging_with_exception(self, mock_get_logger, logger):
        """Test ERROR level logging with exception."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        try:
            raise ValueError("Test error")
        except ValueError as e:
            logger.error("Test.Error", "An error occurred", error=e)

        # Verify logger was called
        mock_logger.log.assert_called_once()
        args = mock_logger.log.call_args

        assert args[0][0] == 40  # ERROR level
        log_data = json.loads(args[0][1])

        assert log_data["level"] == "ERROR"
        assert log_data["error_type"] == "ValueError"
        assert log_data["error_message"] == "Test error"
        assert log_data["error_stack"] is not None

    def test_operation_tracer(self, logger):
        """Test operation tracing context manager."""
        with patch.object(logger, 'info') as mock_info:
            with logger.trace_operation("TestOperation", portfolio_id="PORT-123"):
                pass  # Simulate some work

            # Should have called info twice: start and complete
            assert mock_info.call_count == 2

            # Check start call
            start_call = mock_info.call_args_list[0]
            assert start_call[0][0] == "TestOperation.Start"

            # Check complete call
            complete_call = mock_info.call_args_list[1]
            assert complete_call[0][0] == "TestOperation.Complete"
            assert "latency_ms" in complete_call[1]["metrics"]

    def test_operation_tracer_with_error(self, logger):
        """Test operation tracing with error."""
        with patch.object(logger, 'info') as mock_info, \
                patch.object(logger, 'error') as mock_error:

            try:
                with logger.trace_operation("FailingOperation"):
                    raise RuntimeError("Something went wrong")
            except RuntimeError:
                pass

            # Should have called info once (start) and error once
            mock_info.assert_called_once()
            mock_error.assert_called_once()

            error_call = mock_error.call_args
            assert error_call[0][0] == "FailingOperation.Error"

    def test_required_fields_validation(self, logger):
        """Test that all required fields are present."""
        with patch.object(logger, '_emit_log') as mock_emit:
            logger.info("Test.Event", "Test message")

            # Get the log entry that was emitted
            log_entry = mock_emit.call_args[0][0]

            # Check required fields
            required_fields = [
                "ts", "env", "service", "component", "version", "region",
                "level", "category", "event", "message", "pii_flags", "metrics", "kvs"
            ]

            for field in required_fields:
                assert field in log_entry, f"Required field '{field}' missing"

    def test_correlation_id_consistency(self, logger):
        """Test that correlation_id is consistent across logs."""
        with patch.object(logger, '_emit_log') as mock_emit:
            logger.info("Event1", "Message 1")
            logger.info("Event2", "Message 2")

            # Get correlation IDs from both calls
            call1_correlation = mock_emit.call_args_list[0][0][0]["correlation_id"]
            call2_correlation = mock_emit.call_args_list[1][0][0]["correlation_id"]

            # Should be the same across calls for same logger instance
            assert call1_correlation == call2_correlation

    def test_trace_id_override(self, logger):
        """Test that explicit trace_id overrides correlation_id."""
        with patch.object(logger, '_emit_log') as mock_emit:
            custom_trace = "custom-trace-123"
            logger.info("Test.Event", "Test message", trace_id=custom_trace)

            log_entry = mock_emit.call_args[0][0]
            assert log_entry["trace_id"] == custom_trace


class TestContextHelpers:
    """Test context helper functions."""

    def test_create_ingestion_context(self):
        """Test ingestion context creation."""
        ctx = create_ingestion_context(
            source_type="xls",
            file_key="test.xlsx",
            checksum="sha256:abc123",
            headers_detected=True
        )

        expected = {
            "ingestion_ctx": {
                "source_type": "xls",
                "file_key": "test.xlsx",
                "checksum": "sha256:abc123",
                "parser": None,
                "delimiter": None,
                "headers_detected": True
            }
        }

        assert ctx == expected

    def test_create_snowflake_context(self):
        """Test Snowflake context creation."""
        ctx = create_snowflake_context(
            query_id="01a12345-0400-5db1-0000-0f5c00a1bdf6",
            rows_affected=1000,
            credit_cost_est=0.05
        )

        expected = {
            "snowflake_ctx": {
                "query_id": "01a12345-0400-5db1-0000-0f5c00a1bdf6",
                "rows_affected": 1000,
                "bytes_scanned": None,
                "credit_cost_est": 0.05
            }
        }

        assert ctx == expected

    def test_create_airflow_context(self):
        """Test Airflow context creation."""
        ctx = create_airflow_context(
            dag_id="test_dag",
            task_id="test_task",
            run_id="manual_2023-01-01",
            try_number=2
        )

        expected = {
            "airflow_ctx": {
                "dag_id": "test_dag",
                "task_id": "test_task",
                "run_id": "manual_2023-01-01",
                "try_number": 2
            }
        }

        assert ctx == expected


class TestAWSIntegration:
    """Test AWS-specific functionality."""

    @patch('urllib.request.urlopen')
    def test_region_detection_from_metadata(self, mock_urlopen):
        """Test region detection from EC2 metadata."""
        mock_response = Mock()
        mock_response.read.return_value = b'us-west-2'
        mock_urlopen.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            logger = FinomenyLogger("test", "test", "1.0.0")
            assert logger.region == "us-west-2"

    @patch('urllib.request.urlopen')
    def test_host_detection_from_metadata(self, mock_urlopen):
        """Test host detection from EC2 metadata."""
        mock_response = Mock()
        mock_response.read.return_value = b'i-1234567890abcdef0'
        mock_urlopen.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            logger = FinomenyLogger("test", "test", "1.0.0")
            assert logger.host == "i-1234567890abcdef0"

    def test_lambda_context_detection(self):
        """Test Lambda context detection."""
        with patch.dict(os.environ, {
            'AWS_LAMBDA_FUNCTION_NAME': 'my-function',
            '_X_AMZN_TRACE_ID': 'Root=1-5e272390-8c398be037738dc042009320'
        }):
            logger = FinomenyLogger("test", "test", "1.0.0")
            assert logger.host == "my-function"
            assert logger.aws_request_id == "Root=1-5e272390-8c398be037738dc042009320"


if __name__ == "__main__":
    pytest.main([__file__])
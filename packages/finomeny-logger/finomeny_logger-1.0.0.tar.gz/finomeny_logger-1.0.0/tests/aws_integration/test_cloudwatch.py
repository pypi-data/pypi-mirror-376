"""
CloudWatch Text Handler for Finomeny Logger

Provides specialized CloudWatch integration with batching, retry logic,
and structured log formatting optimized for CloudWatch Logs consumption.
"""

import json
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from collections import deque
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from src.finomeny_logger import FinomenyLogger


class CloudWatchTextHandler:
    """
    CloudWatch Logs handler with batching and retry capabilities.

    Features:
    - Automatic batching of log events
    - Exponential backoff retry logic
    - Sequence token management
    - Log stream auto-creation
    - Memory-efficient queuing
    """

    def __init__(
            self,
            log_group: str,
            log_stream: Optional[str] = None,
            region: Optional[str] = None,
            batch_size: int = 25,
            batch_timeout_seconds: float = 5.0,
            max_retries: int = 3,
            retry_backoff_base: float = 1.0,
            max_queue_size: int = 10000,
            create_log_group: bool = True,
            create_log_stream: bool = True
    ):
        """
        Initialize CloudWatch handler.

        Args:
            log_group: CloudWatch log group name
            log_stream: CloudWatch log stream name (auto-generated if None)
            region: AWS region (auto-detected if None)
            batch_size: Maximum events per batch (1-10000, AWS limit is 10000)
            batch_timeout_seconds: Maximum time to wait before sending partial batch
            max_retries: Maximum retry attempts for failed requests
            retry_backoff_base: Base seconds for exponential backoff
            max_queue_size: Maximum events to queue before dropping oldest
            create_log_group: Whether to create log group if it doesn't exist
            create_log_stream: Whether to create log stream if it doesn't exist
        """
        self.log_group = log_group
        self.log_stream = log_stream or self._generate_log_stream_name()
        self.batch_size = min(batch_size, 10000)  # AWS limit
        self.batch_timeout_seconds = batch_timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.max_queue_size = max_queue_size
        self.create_log_group = create_log_group
        self.create_log_stream = create_log_stream

        # Initialize AWS client
        self.region = region or self._detect_region()
        try:
            self.cloudwatch_logs = boto3.client('logs', region_name=self.region)
        except NoCredentialsError:
            raise RuntimeError("AWS credentials not found. Configure credentials for CloudWatch logging.")

        # State management
        self.sequence_token = None
        self.log_queue = deque(maxlen=max_queue_size)
        self.queue_lock = threading.Lock()
        self.last_flush_time = time.time()

        # Background thread for batching
        self.flush_thread = None
        self.shutdown_event = threading.Event()
        self._start_flush_thread()

        # Setup log group/stream
        self._setup_cloudwatch_resources()

    def _detect_region(self) -> str:
        """Detect AWS region from environment or metadata."""
        import os
        region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION')
        if region:
            return region

        try:
            import urllib.request
            response = urllib.request.urlopen(
                'http://169.254.169.254/latest/meta-data/placement/region',
                timeout=2
            )
            return response.read().decode('utf-8')
        except:
            return 'us-east-1'

    def _generate_log_stream_name(self) -> str:
        """Generate unique log stream name."""
        import os
        import socket

        # Try Lambda function name first
        lambda_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        if lambda_name:
            timestamp = datetime.now(timezone.utc).strftime('%Y/%m/%d')
            return f"{lambda_name}/{timestamp}/[{os.environ.get('AWS_LAMBDA_LOG_STREAM_NAME', 'unknown')}]"

        # Fallback to hostname + timestamp
        hostname = socket.gethostname()
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')
        return f"{hostname}/{timestamp}"

    def _setup_cloudwatch_resources(self):
        """Create log group and stream if they don't exist."""
        try:
            # Create log group
            if self.create_log_group:
                try:
                    self.cloudwatch_logs.create_log_group(logGroupName=self.log_group)
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                        raise

            # Create log stream
            if self.create_log_stream:
                try:
                    self.cloudwatch_logs.create_log_stream(
                        logGroupName=self.log_group,
                        logStreamName=self.log_stream
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                        raise

            # Get initial sequence token
            self._update_sequence_token()

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            raise RuntimeError(f"Failed to setup CloudWatch resources: {error_code} - {str(e)}")

    def _update_sequence_token(self):
        """Update sequence token from CloudWatch."""
        try:
            response = self.cloudwatch_logs.describe_log_streams(
                logGroupName=self.log_group,
                logStreamNamePrefix=self.log_stream
            )

            for stream in response.get('logStreams', []):
                if stream['logStreamName'] == self.log_stream:
                    self.sequence_token = stream.get('uploadSequenceToken')
                    break

        except ClientError:
            # If we can't get sequence token, it will be updated on next put attempt
            pass

    def _start_flush_thread(self):
        """Start background thread for periodic flushing."""
        if self.flush_thread and self.flush_thread.is_alive():
            return

        self.shutdown_event.clear()
        self.flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
        self.flush_thread.start()

    def _flush_worker(self):
        """Background worker for periodic log flushing."""
        while not self.shutdown_event.is_set():
            try:
                current_time = time.time()
                time_since_flush = current_time - self.last_flush_time

                # Check if we should flush based on timeout or queue size
                with self.queue_lock:
                    should_flush = (
                            len(self.log_queue) >= self.batch_size or
                            (len(self.log_queue) > 0 and time_since_flush >= self.batch_timeout_seconds)
                    )

                if should_flush:
                    self._flush_logs()

                # Sleep for a short interval
                self.shutdown_event.wait(0.1)

            except Exception as e:
                # Log error but keep thread alive
                print(f"CloudWatch flush worker error: {e}", file=sys.stderr)
                self.shutdown_event.wait(1.0)

    def emit_log(self, log_entry: Dict[str, Any]):
        """
        Queue log entry for CloudWatch delivery.

        Args:
            log_entry: Structured log entry from FinomenyLogger
        """
        # Convert to CloudWatch log event
        log_event = {
            'timestamp': self._get_timestamp_ms(log_entry.get('ts')),
            'message': json.dumps(log_entry, default=str, separators=(',', ':'))
        }

        # Add to queue
        with self.queue_lock:
            self.log_queue.append(log_event)

            # Trigger immediate flush if queue is full
            if len(self.log_queue) >= self.batch_size:
                threading.Thread(target=self._flush_logs, daemon=True).start()

    def _get_timestamp_ms(self, iso_timestamp: str) -> int:
        """Convert ISO timestamp to milliseconds since epoch."""
        try:
            dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        except:
            return int(time.time() * 1000)

    def _flush_logs(self):
        """Flush queued logs to CloudWatch."""
        # Get batch of events to send
        events_to_send = []
        with self.queue_lock:
            if not self.log_queue:
                return

            # Take up to batch_size events
            for _ in range(min(self.batch_size, len(self.log_queue))):
                events_to_send.append(self.log_queue.popleft())

        if not events_to_send:
            return

        # Sort events by timestamp (required by CloudWatch)
        events_to_send.sort(key=lambda x: x['timestamp'])

        # Send with retry logic
        success = self._send_logs_with_retry(events_to_send)

        if not success:
            # If all retries failed, we've already logged the error
            # Events are lost - could implement dead letter queue here
            pass

        self.last_flush_time = time.time()

    def _send_logs_with_retry(self, events: List[Dict[str, Any]]) -> bool:
        """Send logs to CloudWatch with exponential backoff retry."""
        for attempt in range(self.max_retries + 1):
            try:
                # Prepare request
                put_events_kwargs = {
                    'logGroupName': self.log_group,
                    'logStreamName': self.log_stream,
                    'logEvents': events
                }

                if self.sequence_token:
                    put_events_kwargs['sequenceToken'] = self.sequence_token

                # Send to CloudWatch
                response = self.cloudwatch_logs.put_log_events(**put_events_kwargs)

                # Update sequence token for next request
                self.sequence_token = response.get('nextSequenceToken')

                # Check for rejected events
                rejected_count = len(response.get('rejectedLogEvents', []))
                if rejected_count > 0:
                    print(f"CloudWatch rejected {rejected_count} log events", file=sys.stderr)

                return True

            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')

                # Handle sequence token errors
                if error_code in ['InvalidSequenceTokenException', 'DataAlreadyAcceptedException']:
                    self._update_sequence_token()
                    if attempt < self.max_retries:
                        continue

                # Handle throttling
                if error_code == 'ThrottlingException':
                    if attempt < self.max_retries:
                        backoff_time = self.retry_backoff_base * (2 ** attempt)
                        time.sleep(backoff_time)
                        continue

                # Log error
                if attempt == self.max_retries:
                    print(
                        f"CloudWatch put_log_events failed after {self.max_retries + 1} attempts: {error_code} - {str(e)}",
                        file=sys.stderr)

            except Exception as e:
                if attempt == self.max_retries:
                    print(f"Unexpected error sending logs to CloudWatch: {str(e)}", file=sys.stderr)
                else:
                    backoff_time = self.retry_backoff_base * (2 ** attempt)
                    time.sleep(backoff_time)

        return False

    def flush(self):
        """Immediately flush all queued logs."""
        self._flush_logs()

    def close(self):
        """Close handler and flush remaining logs."""
        # Signal shutdown
        self.shutdown_event.set()

        # Wait for flush thread to finish
        if self.flush_thread and self.flush_thread.is_alive():
            self.flush_thread.join(timeout=5.0)

        # Final flush
        self.flush()


class CloudWatchFinomenyLogger(FinomenyLogger):
    """
    Extended FinomenyLogger with CloudWatch integration.

    Combines structured logging with direct CloudWatch delivery,
    bypassing local logging infrastructure for critical applications.
    """

    def __init__(
            self,
            service: str,
            component: str,
            version: str,
            log_group: str,
            log_stream: Optional[str] = None,
            enable_cloudwatch: bool = True,
            cloudwatch_config: Optional[Dict[str, Any]] = None,
            **kwargs
    ):
        """
        Initialize CloudWatch-enabled logger.

        Args:
            service: Service name
            component: Component type
            version: Service version
            log_group: CloudWatch log group name
            log_stream: CloudWatch log stream name (auto-generated if None)
            enable_cloudwatch: Whether to enable CloudWatch handler
            cloudwatch_config: Additional CloudWatch handler configuration
            **kwargs: Additional arguments passed to FinomenyLogger
        """
        super().__init__(service, component, version, **kwargs)

        self.cloudwatch_handler = None

        if enable_cloudwatch:
            cw_config = cloudwatch_config or {}
            cw_config.update({
                'log_group': log_group,
                'log_stream': log_stream,
                'region': self.region
            })

            try:
                self.cloudwatch_handler = CloudWatchTextHandler(**cw_config)
            except Exception as e:
                # Log error but don't fail initialization
                print(f"Failed to initialize CloudWatch handler: {e}", file=sys.stderr)
                self.cloudwatch_handler = None

    def _emit_log(self, log_entry: Dict[str, Any]) -> None:
        """Override to emit to both standard logger and CloudWatch."""
        # Standard logging (CloudWatch via Lambda/EC2 agents)
        super()._emit_log(log_entry)

        # Direct CloudWatch logging
        if self.cloudwatch_handler:
            try:
                self.cloudwatch_handler.emit_log(log_entry)
            except Exception as e:
                # Don't fail the log call, but report the error
                print(f"CloudWatch handler error: {e}", file=sys.stderr)

    def flush_cloudwatch(self):
        """Flush pending CloudWatch logs immediately."""
        if self.cloudwatch_handler:
            self.cloudwatch_handler.flush()

    def close(self):
        """Close logger and flush remaining logs."""
        if self.cloudwatch_handler:
            self.cloudwatch_handler.close()


# Convenience factory function
def create_cloudwatch_logger(
        service: str,
        component: str,
        version: str,
        log_group_prefix: str = "finomeny",
        **kwargs
) -> CloudWatchFinomenyLogger:
    """
    Factory function for creating CloudWatch-enabled loggers.

    Args:
        service: Service name (e.g., 'portfolio-ingester')
        component: Component type (e.g., 'lambda', 'airflow')
        version: Service version
        log_group_prefix: Prefix for log group name
        **kwargs: Additional configuration

    Returns:
        Configured CloudWatchFinomenyLogger instance
    """
    log_group = f"/{log_group_prefix}/{service}"

    return CloudWatchFinomenyLogger(
        service=service,
        component=component,
        version=version,
        log_group=log_group,
        **kwargs
    )


# Example usage
if __name__ == "__main__":
    import sys

    # Create logger
    logger = create_cloudwatch_logger(
        service="test-service",
        component="lambda",
        version="1.0.0"
    )

    # Test logging
    logger.info(
        "TestEvent",
        "Testing CloudWatch integration",
        metrics={"test_metric": 123},
        kvs={"test_key": "test_value"}
    )

    # Test error logging
    try:
        raise ValueError("Test error for CloudWatch")
    except Exception as e:
        logger.error(
            "TestError",
            "Testing error logging to CloudWatch",
            error=e
        )

    # Flush and close
    logger.flush_cloudwatch()
    logger.close()

    print("CloudWatch logging test completed")
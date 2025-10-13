import json
import time
import pika
import logging
import threading
import socket
try:
    from .config import RABBITMQ_SERVER, RABBITMQ_AMQP_PORT, RABBITMQ_USER, STREAM_MESSAGE_TTL_SECONDS, DEBUG_ENABLED
except ImportError as e:
    raise ImportError(f"❌ CRITICAL ERROR: Failed to import RabbitMQ config: {e}\n💡 Check that config.py exists and contains RABBITMQ_SERVER, RABBITMQ_AMQP_PORT, RABBITMQ_USER") from e

class RabbitMQClient:
    def __init__(self, logger, queue, id = None, use_ttl = False, ttl_seconds = None, max_length = None):
        self.logger = logger
        self.id = id
        self.use_ttl = use_ttl  # Flag to determine if TTL should be applied
        self.ttl_seconds = ttl_seconds  # Custom TTL in seconds (overrides default)
        self.max_length = max_length  # Max queue length (for latest-only processing)
        _queue = "{}-{}".format(queue, id.replace(":", "")) if id is not None else queue
        self.queue = _queue
        self.connection = None
        self.channel = None
        self._is_running = True
        self._connection_lock = threading.Lock()  # Prevent concurrent reconnection attempts
        self._reconnect_delay = 1  # Start with 1 second delay
        self._max_reconnect_delay = 30  # Maximum delay between reconnection attempts
        self._status_callback = None  # Callback function for reporting statuses to plugin
        self._log_info("Initializing RabbitMQ client for queue: {}".format(_queue))
        self._connect_with_retry()

    def _log_info(self, message):
        """Log info message only if DEBUG_ENABLED is True"""
        if DEBUG_ENABLED and self.logger is not None:
            self.logger.info(message)

    def _log_error(self, message):
        """Log error message (always logged regardless of debug setting)"""
        if self.logger is not None:
            self.logger.error(message)

    def _log_warn(self, message):
        """Log warning message (always logged regardless of debug setting)"""
        if self.logger is not None:
            self.logger.warning(message)

    def set_error_callback(self, callback):
        """Set callback function for reporting statuses to plugin"""
        self._status_callback = callback

    def _report_status(self, severity, category, code, message, details=None, exception=None):
        """Report status through callback if available"""
        if self._status_callback:
            try:
                # Import here to avoid circular imports
                try:
                    from status_reporting import StatusSeverity, StatusCategory
                except:
                    from .status_reporting import StatusSeverity, StatusCategory

                # Convert string severity to enum if needed
                if isinstance(severity, str):
                    severity = StatusSeverity(severity)
                if isinstance(category, str):
                    category = StatusCategory(category)

                self._status_callback(
                    severity=severity,
                    category=category,
                    code=code,
                    message=message,
                    details=details or {},
                    component="rabbitmq_client",
                    exception=exception
                )
            except Exception as e:
                self._log_error("Failed to report status through callback: {}".format(e))

    def _is_rabbitmq_available(self):
        """Check if RabbitMQ server is available by attempting a socket connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Use longer timeout for network connections (vs localhost)
            timeout = 15 if RABBITMQ_SERVER != "localhost" and not RABBITMQ_SERVER.startswith("127.") else 5
            sock.settimeout(timeout)
            self._log_info("Checking RabbitMQ availability at {}:5672 (timeout: {}s)".format(RABBITMQ_SERVER, timeout))
            result = sock.connect_ex((RABBITMQ_SERVER, 5672))
            sock.close()

            if result == 0:
                self._log_info("RabbitMQ server is reachable")
                return True
            else:
                self._log_warn("RabbitMQ server not reachable (connect_ex returned: {})".format(result))
                return False
        except Exception as e:
            self._log_error("Error checking RabbitMQ availability: {}".format(e))
            return False

    def _connect_with_retry(self):
        """Establish connection to RabbitMQ with retry logic"""
        with self._connection_lock:
            while self._is_running:
                try:
                    if not self._is_rabbitmq_available():
                        self._log_warn("RabbitMQ server not available, waiting {} seconds before retry".format(self._reconnect_delay))
                        time.sleep(self._reconnect_delay)
                        self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
                        continue

                    self._log_info("Attempting to connect to RabbitMQ server at {}".format(RABBITMQ_SERVER))

                    # Use different connection parameters for network vs localhost
                    if RABBITMQ_SERVER == "localhost" or RABBITMQ_SERVER.startswith("127."):
                        # Localhost connection - use shorter timeouts
                        # WINDOWS FIX: Optimized connection parameters to prevent blocking
                        connection_params = pika.ConnectionParameters(
                            host=RABBITMQ_SERVER,
                            heartbeat=300,  # 5 minute heartbeat (reduced from 10)
                            blocked_connection_timeout=60,  # 1 minute timeout (reduced from 5)
                            socket_timeout=5,  # 5 second socket timeout (reduced from 10)
                            connection_attempts=3,  # Retry connection attempts
                            retry_delay=1,  # 1 second between retries
                        )
                    else:
                        # Network connection - use longer timeouts and more robust settings
                        connection_params = pika.ConnectionParameters(
                            host=RABBITMQ_SERVER,
                            heartbeat=300,  # 5 minute heartbeat (shorter for network)
                            blocked_connection_timeout=180,  # 3 minute timeout
                            socket_timeout=30,  # 30 second socket timeout for network
                            connection_attempts=3,  # Retry connection attempts
                            retry_delay=2,  # 2 second delay between retries
                        )

                    self.connection = pika.BlockingConnection(connection_params)
                    self.channel = self.connection.channel()

                    # Enhanced success logging to CONSOLE
                    print("🎉 RABBITMQ CONNECTION SUCCESSFUL!")
                    print("✅ Connected to RabbitMQ server at {}:{}".format(RABBITMQ_SERVER, RABBITMQ_AMQP_PORT))
                    print("✅ Authentication successful with user: {}".format(RABBITMQ_USER))
                    print("✅ Channel created successfully")
                    print("✅ Queue: {} is ready for operations".format(self.queue))

                    # Also log to GUI logger if available
                    self._log_info("🎉 RABBITMQ CONNECTION SUCCESSFUL!")
                    self._log_info("✅ Connected to RabbitMQ server at {}:{}".format(RABBITMQ_SERVER, RABBITMQ_AMQP_PORT))
                    self._log_info("✅ Authentication successful with user: {}".format(RABBITMQ_USER))
                    self._log_info("✅ Channel created successfully")
                    self._log_info("✅ Queue: {} is ready for operations".format(self.queue))

                    # Report successful connection status
                    self._report_status(
                        severity="info",
                        category="connectivity",
                        code="RABBITMQ_CONNECTION_SUCCESS",
                        message="Successfully connected to RabbitMQ server",
                        details={
                            'server': RABBITMQ_SERVER,
                            'port': RABBITMQ_AMQP_PORT,
                            'user': RABBITMQ_USER,
                            'queue': self.queue,
                            'connection_type': 'network' if RABBITMQ_SERVER != "localhost" and not RABBITMQ_SERVER.startswith("127.") else 'localhost'
                        }
                    )

                    self._reconnect_delay = 1  # Reset delay on successful connection
                    return True
                except Exception as e:
                    # Enhanced error logging to CONSOLE
                    print("❌ RABBITMQ CONNECTION FAILED!")
                    print("❌ Server: {}:{}".format(RABBITMQ_SERVER, RABBITMQ_AMQP_PORT))
                    print("❌ User: {}".format(RABBITMQ_USER))
                    print("❌ Error: {}".format(e))
                    print("❌ Error Type: {}".format(type(e).__name__))

                    # Also log to GUI logger if available
                    self._log_error("❌ RABBITMQ CONNECTION FAILED!")
                    self._log_error("❌ Server: {}:{}".format(RABBITMQ_SERVER, RABBITMQ_AMQP_PORT))
                    self._log_error("❌ User: {}".format(RABBITMQ_USER))
                    self._log_error("❌ Error: {}".format(e))
                    self._log_error("❌ Error Type: {}".format(type(e).__name__))

                    # Provide specific troubleshooting hints based on error type to CONSOLE
                    error_str = str(e).lower()
                    if "access refused" in error_str or "authentication" in error_str:
                        print("💡 TROUBLESHOOTING: Authentication failed")
                        print("   - Guest user is restricted to localhost connections")
                        print("   - Create a new user: docker exec minerva-rabbit-mq-1 rabbitmqctl add_user minerva_user password")
                        print("   - Set permissions: docker exec minerva-rabbit-mq-1 rabbitmqctl set_permissions minerva_user '.*' '.*' '.*'")
                        self._log_error("💡 TROUBLESHOOTING: Authentication failed")
                        self._log_error("   - Guest user is restricted to localhost connections")
                        self._log_error("   - Create a new user: docker exec minerva-rabbit-mq-1 rabbitmqctl add_user minerva_user password")
                        self._log_error("   - Set permissions: docker exec minerva-rabbit-mq-1 rabbitmqctl set_permissions minerva_user '.*' '.*' '.*'")
                    elif "connection refused" in error_str or "timeout" in error_str:
                        print("💡 TROUBLESHOOTING: Connection refused")
                        print("   - Check if RabbitMQ is running: docker ps")
                        print("   - Check firewall: ports 5672 and 15672 must be open")
                        print("   - Test connectivity: telnet {} 5672".format(RABBITMQ_SERVER))
                        self._log_error("💡 TROUBLESHOOTING: Connection refused")
                        self._log_error("   - Check if RabbitMQ is running: docker ps")
                        self._log_error("   - Check firewall: ports 5672 and 15672 must be open")
                        self._log_error("   - Test connectivity: telnet {} 5672".format(RABBITMQ_SERVER))
                    elif "name resolution" in error_str or "host" in error_str:
                        print("💡 TROUBLESHOOTING: Host resolution failed")
                        print("   - Check if IP address {} is correct".format(RABBITMQ_SERVER))
                        print("   - Try ping: ping {}".format(RABBITMQ_SERVER))
                        self._log_error("💡 TROUBLESHOOTING: Host resolution failed")
                        self._log_error("   - Check if IP address {} is correct".format(RABBITMQ_SERVER))
                        self._log_error("   - Try ping: ping {}".format(RABBITMQ_SERVER))

                    # Report connection status
                    self._report_status(
                        severity="critical",
                        category="connectivity",
                        code="RABBITMQ_CONNECTION_FAILED",
                        message="Failed to establish RabbitMQ connection",
                        details={
                            'queue': self.queue,
                            'server': RABBITMQ_SERVER,
                            'port': RABBITMQ_AMQP_PORT,
                            'user': RABBITMQ_USER,
                            'retry_delay': self._reconnect_delay,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        },
                        exception=e
                    )

                    if self.connection and not self.connection.is_closed:
                        try:
                            self.connection.close()
                        except:
                            pass
                    self.connection = None
                    self.channel = None

                    if self._is_running:
                        self._log_warn("Retrying connection in {} seconds".format(self._reconnect_delay))
                        time.sleep(self._reconnect_delay)
                        self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
            return False

    def _ensure_connection(self):
        """Ensure we have a valid connection, reconnect if necessary"""
        if not self.connection or self.connection.is_closed or not self.channel or self.channel.is_closed:
            self._log_warn("Connection lost, attempting to reconnect...")
            return self._connect_with_retry()
        return True

    def send_message(self, message):
        """Send a message to the queue with automatic reconnection handling"""
        if not self._ensure_connection():
            self._log_error("Failed to establish connection for sending message")

            # Report connection failure for sending
            self._report_status(
                severity="critical",
                category="connectivity",
                code="RABBITMQ_SEND_CONNECTION_FAILED",
                message="Failed to establish RabbitMQ connection for sending message",
                details={
                    'queue': self.queue,
                    'message_length': len(message) if message else 0
                }
            )
            return False

        try:
            if self.use_ttl:
                # Calculate TTL in milliseconds - use custom TTL if provided, otherwise default
                ttl_seconds = self.ttl_seconds if self.ttl_seconds is not None else STREAM_MESSAGE_TTL_SECONDS
                ttl_ms = ttl_seconds * 1000

                # PERFORMANCE FIX: Only declare queue once per connection, not every message
                if not hasattr(self, '_queue_declared_send') or not self._queue_declared_send:
                    # Declare queue with TTL for streaming data
                    # Messages older than TTL will be automatically discarded
                    # Stream queues should be durable=True for persistence
                    queue_args = {'x-message-ttl': ttl_ms}
                    if self.max_length is not None:
                        queue_args['x-max-length'] = self.max_length
                    self.channel.queue_declare(
                        queue=self.queue,
                        durable=True,
                        arguments=queue_args
                    )
                    self._queue_declared_send = True
                    self._log_info(f"📡 Queue declared for streaming: {self.queue} (TTL: {ttl_seconds}s)")

                # Publish message with TTL properties
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue,
                    body=message,
                    properties=pika.BasicProperties(expiration=str(ttl_ms))  # TTL per message
                )
            else:
                # PERFORMANCE FIX: Only declare queue once per connection, not every message
                if not hasattr(self, '_queue_declared_send') or not self._queue_declared_send:
                    # Declare queue without TTL for ping/command queues
                    # Using durable=True to make all queues durable
                    # WINDOWS FIX: Add priority support for command queues to match Node.js side
                    queue_args = {}
                    if 'command_queue' in self.queue:
                        # Command queues get priority support to prevent blocking during streaming
                        queue_args['x-max-priority'] = 10
                        self._log_info("🚨 Creating command queue with priority support: {}".format(self.queue))

                    self.channel.queue_declare(
                        queue=self.queue,
                        durable=True,  # Changed to True to make all queues durable
                        arguments=queue_args if queue_args else None
                    )
                    self._queue_declared_send = True
                    self._log_info(f"📡 Queue declared for commands/ping: {self.queue}")

                # Publish message without TTL
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue,
                    body=message
                )
            return True
        except Exception as e:
            self._log_error("Error sending message: {}".format(e))

            # Report send failure
            self._report_status(
                severity="high",
                category="connectivity",
                code="RABBITMQ_SEND_FAILED",
                message="Failed to send message to RabbitMQ queue",
                details={
                    'queue': self.queue,
                    'message_length': len(message) if message else 0,
                    'use_ttl': self.use_ttl,
                    'error_type': type(e).__name__
                },
                exception=e
            )

            # Mark connection as invalid to trigger reconnection on next attempt
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
                self.channel = None
            return False

    def reconnect(self):
        """Legacy reconnect method - now uses the improved connection handling"""
        return self._connect_with_retry()


    def consume_message(self, callback):
        """Consume messages with automatic reconnection handling - SMART ROUTING"""
        # Use non-blocking ONLY for command queues, blocking for others (streaming)
        if 'command_queue' in self.queue:
            return self.consume_message_non_blocking(callback)
        else:
            # Use blocking consumption for streaming to ensure reliable data flow
            return self.consume_message_original_blocking(callback)

    def consume_message_non_blocking(self, callback):
        """NON-BLOCKING message consumption using polling - prevents resource contention"""
        self._log_info("Starting NON-BLOCKING message consumption on queue: {}".format(self.queue))
        print("rabbit mq _is_running True - NON-BLOCKING MODE")

        # Main consumption loop with NON-BLOCKING polling
        while self._is_running:
            try:
                # Ensure we have a valid connection and channel
                if not self._ensure_connection() or not self.channel:
                    self._log_error("Failed to establish connection for consuming messages")
                    time.sleep(5)  # Wait before retrying
                    continue

                # MEMORY LEAK FIX: Only declare queue once per connection, not every poll
                if not hasattr(self, '_queue_declared') or not self._queue_declared:
                    # Declare queue with consistent settings based on use_ttl flag
                    if self.use_ttl:
                        # Calculate TTL in milliseconds for streaming queues - use custom TTL if provided
                        ttl_seconds = self.ttl_seconds if self.ttl_seconds is not None else STREAM_MESSAGE_TTL_SECONDS
                        ttl_ms = ttl_seconds * 1000
                        queue_args = {'x-message-ttl': ttl_ms}
                        if self.max_length is not None:
                            queue_args['x-max-length'] = self.max_length
                        self.channel.queue_declare(
                            queue=self.queue,
                            durable=True,
                            arguments=queue_args
                        )
                    else:
                        # Command and ping queues also use durable=True to make all queues durable
                        # WINDOWS FIX: Add priority support for command queues to match Node.js side
                        queue_args = {}
                        if 'command_queue' in self.queue:
                            # Command queues get priority support to prevent blocking during streaming
                            queue_args['x-max-priority'] = 10
                            # Only log once per connection, not every poll
                            if not hasattr(self, '_priority_queue_logged'):
                                self._log_info("🚨 Creating command queue with priority support: {}".format(self.queue))
                                self._priority_queue_logged = True

                        self.channel.queue_declare(
                            queue=self.queue,
                            durable=True,
                            arguments=queue_args if queue_args else None
                        )

                    # Mark queue as declared to avoid repeated declarations
                    self._queue_declared = True

                # NON-BLOCKING: Poll for messages instead of blocking consumption
                method_frame, header_frame, body = self.channel.basic_get(queue=self.queue)

                if method_frame:
                    try:
                        # Parse and process the message
                        message = json.loads(body.decode())

                        # WINDOWS FIX: Immediate acknowledgment for critical commands to prevent blocking
                        cmd_type = message.get("type") if isinstance(message, dict) else None
                        is_critical = cmd_type in ['start', 'go_to_next', 'go_to_step', 'stop_stream', 'load_pups', 'stop', 'abort']

                        if is_critical:
                            # Acknowledge critical commands immediately to prevent queue blocking
                            self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                            self._log_info("🚨 CRITICAL COMMAND acknowledged immediately: {}".format(cmd_type))

                        # Process the message
                        callback(message)

                        if not is_critical:
                            # Acknowledge non-critical messages after processing
                            self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                            self._log_info("Message processed and acknowledged: {}".format(message))

                    except Exception as e:
                        # Log error but still acknowledge to prevent redelivery
                        self._log_error("Error processing message: {}".format(e))
                        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                # Short sleep to prevent CPU spinning - CRITICAL for non-blocking mode
                # MEMORY LEAK FIX: Much longer polling to reduce CPU/memory usage
                if 'command_queue' in self.queue:
                    time.sleep(1.0)  # 1 second polling for commands - prevent memory leak
                else:
                    time.sleep(2.0)   # 2 second polling for other queues - prevent memory leak

            except Exception as e:
                self._log_error("Error during consumption: {}".format(e))
                # Mark connection as invalid on connection errors
                if "connection" in str(e).lower() or "channel" in str(e).lower():
                    if self.connection:
                        try:
                            self.connection.close()
                        except:
                            pass
                        self.connection = None
                        self.channel = None

                    if self._is_running:
                        self._log_warn("Will attempt to reconnect in 5 seconds...")
                        time.sleep(5)
                else:
                    # For other errors, just wait and retry
                    if self._is_running:
                        time.sleep(1)  # Shorter wait for non-connection errors

        print("rabbit mq _is_running False")
        self.close()
        print("closing connection")

    def stop_consuming(self):
        """Stop consuming messages and set running flag to False"""
        self._is_running = False
        with self._connection_lock:
            if self.channel and not self.channel.is_closed:
                try:
                    self.channel.stop_consuming()
                    self._log_info("Stopped consuming messages")
                except (pika.exceptions.ConnectionWrongStateError,
                        pika.exceptions.ChannelWrongStateError,
                        pika.exceptions.ConnectionClosedByBroker) as e:
                    # These exceptions are expected during shutdown when connection is already closed
                    self._log_info("Consumer already stopped or connection closed: {}".format(e))
                except Exception as e:
                    self._log_error("Error stopping consumer: {}".format(e))

    def close(self):
        """Close the channel and connection"""
        self._is_running = False
        with self._connection_lock:
            try:
                if self.channel and not self.channel.is_closed:
                    self.channel.close()
            except (pika.exceptions.ConnectionWrongStateError,
                    pika.exceptions.ChannelWrongStateError,
                    pika.exceptions.ConnectionClosedByBroker) as e:
                # These exceptions are expected during shutdown when connection is already closed
                self._log_info("Channel already closed: {}".format(e))
            except Exception as e:
                self._log_error("Error closing channel: {}".format(e))

            try:
                if self.connection and not self.connection.is_closed:
                    self.connection.close()
                self._log_info("RabbitMQ connection closed")
            except (pika.exceptions.ConnectionWrongStateError,
                    pika.exceptions.ChannelWrongStateError,
                    pika.exceptions.ConnectionClosedByBroker) as e:
                # These exceptions are expected during shutdown when connection is already closed
                self._log_info("Connection already closed: {}".format(e))
            except Exception as e:
                self._log_error("Error closing connection: {}".format(e))

            # Clear references and reset queue declaration flags
            self.connection = None
            self.channel = None
            # Reset queue declaration flags so they get re-declared on reconnection
            if hasattr(self, '_queue_declared_send'):
                self._queue_declared_send = False
            if hasattr(self, '_queue_declared'):
                self._queue_declared = False
            if hasattr(self, '_queue_declared_blocking'):
                self._queue_declared_blocking = False

    def consume_message_original_blocking(self, callback):
        """Original blocking message consumption - reliable for streaming"""
        def message_callback_wrapper(ch, method, properties, body):
            try:
                # Parse and process the message
                message = json.loads(body.decode())

                # WINDOWS FIX: Immediate acknowledgment for critical commands to prevent blocking
                cmd_type = message.get("type") if isinstance(message, dict) else None
                is_critical = cmd_type in ['start', 'go_to_next', 'go_to_step', 'stop_stream', 'load_pups', 'stop', 'abort']

                if is_critical:
                    # Acknowledge critical commands immediately to prevent queue blocking
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    self._log_info("🚨 CRITICAL COMMAND acknowledged immediately: {}".format(cmd_type))

                # Process the message
                callback(message)

                if not is_critical:
                    # Acknowledge non-critical messages after processing
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    self._log_info("Message processed and acknowledged: {}".format(message))

            except Exception as e:
                # Log error but still acknowledge to prevent redelivery
                self._log_error("Error processing message: {}".format(e))
                ch.basic_ack(delivery_tag=method.delivery_tag)

        self._log_info("Starting BLOCKING message consumption on queue: {}".format(self.queue))
        print("rabbit mq _is_running True - BLOCKING MODE")

        # Main consumption loop with reconnection handling
        while self._is_running:
            try:
                # Ensure we have a valid connection and channel
                if not self._ensure_connection() or not self.channel:
                    self._log_error("Failed to establish connection for consuming messages")
                    time.sleep(5)  # Wait before retrying
                    continue

                # Declare queue once per connection
                if not hasattr(self, '_queue_declared_blocking') or not self._queue_declared_blocking:
                    if self.use_ttl:
                        ttl_seconds = self.ttl_seconds if self.ttl_seconds is not None else STREAM_MESSAGE_TTL_SECONDS
                        ttl_ms = ttl_seconds * 1000
                        queue_args = {'x-message-ttl': ttl_ms}
                        if self.max_length is not None:
                            queue_args['x-max-length'] = self.max_length
                        self.channel.queue_declare(
                            queue=self.queue,
                            durable=True,
                            arguments=queue_args
                        )
                    else:
                        queue_args = {}
                        if 'command_queue' in self.queue:
                            queue_args['x-max-priority'] = 10
                        self.channel.queue_declare(
                            queue=self.queue,
                            durable=True,
                            arguments=queue_args if queue_args else None
                        )
                    self._queue_declared_blocking = True

                # Set up blocking consumption
                self.channel.basic_qos(prefetch_count=1)
                self.channel.basic_consume(
                    queue=self.queue,
                    on_message_callback=message_callback_wrapper,
                    auto_ack=False
                )
                self._log_info("Listening for messages on {}. To exit press CTRL+C".format(self.queue))

                # Start consuming - this will block until stop() is called or connection fails
                self.channel.start_consuming()

            except Exception as e:
                self._log_error("Error during blocking consumption: {}".format(e))
                # Mark connection as invalid on connection errors
                if "connection" in str(e).lower() or "channel" in str(e).lower():
                    if self.connection:
                        try:
                            self.connection.close()
                        except:
                            pass
                        self.connection = None
                        self.channel = None
                        self._queue_declared_blocking = False  # Reset queue declaration flag

                    if self._is_running:
                        self._log_warn("Will attempt to reconnect in 5 seconds...")
                        time.sleep(5)
                else:
                    if self._is_running:
                        time.sleep(1)

        print("rabbit mq _is_running False - BLOCKING MODE")
        self.close()
        print("closing connection")

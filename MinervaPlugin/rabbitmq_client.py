import json
import time
import pika
import logging
import threading
import socket
try:
    from config import RABBITMQ_SERVER, STREAM_MESSAGE_TTL_SECONDS
except:
    from .config import RABBITMQ_SERVER, STREAM_MESSAGE_TTL_SECONDS

# Debug toggle - set to False to disable all debug logs
DEBUG_ENABLED = True

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

    def _is_rabbitmq_available(self):
        """Check if RabbitMQ server is available by attempting a socket connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            result = sock.connect_ex((RABBITMQ_SERVER, 5672))
            sock.close()
            return result == 0
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

                    self._log_info("Attempting to connect to RabbitMQ server")
                    self.connection = pika.BlockingConnection(
                        pika.ConnectionParameters(
                            host=RABBITMQ_SERVER,
                            heartbeat=600,  # 10 minute heartbeat
                            blocked_connection_timeout=300,  # 5 minute timeout
                        )
                    )
                    self.channel = self.connection.channel()
                    self._log_info("Successfully connected to RabbitMQ server")
                    self._reconnect_delay = 1  # Reset delay on successful connection
                    return True
                except Exception as e:
                    self._log_error("Failed to connect to RabbitMQ: {}".format(e))
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
            return False

        try:
            if self.use_ttl:
                # Calculate TTL in milliseconds - use custom TTL if provided, otherwise default
                ttl_seconds = self.ttl_seconds if self.ttl_seconds is not None else STREAM_MESSAGE_TTL_SECONDS
                ttl_ms = ttl_seconds * 1000

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
                # Publish message with TTL properties
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue,
                    body=message,
                    properties=pika.BasicProperties(expiration=str(ttl_ms))  # TTL per message
                )
            else:
                # Declare queue without TTL for ping/command queues
                # Using durable=True to make all queues durable
                self.channel.queue_declare(
                    queue=self.queue,
                    durable=True  # Changed to True to make all queues durable
                )
                # Publish message without TTL
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue,
                    body=message
                )
            return True
        except Exception as e:
            self._log_error("Error sending message: {}".format(e))
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
        """Consume messages with automatic reconnection handling"""
        def message_callback_wrapper(ch, method, properties, body):
            try:
                # Parse and process the message
                message = json.loads(body.decode())
                callback(message)
                # Acknowledge the message after successful processing
                ch.basic_ack(delivery_tag=method.delivery_tag)
                self._log_info("Message processed and acknowledged: {}".format(message))
            except Exception as e:
                # Log error but still acknowledge to prevent redelivery
                self._log_error("Error processing message: {}".format(e))
                ch.basic_ack(delivery_tag=method.delivery_tag)

        self._log_info("Starting message consumption on queue: {}".format(self.queue))
        print("rabbit mq _is_running True")

        # Main consumption loop with reconnection handling
        while self._is_running:
            try:
                # Ensure we have a valid connection
                if not self._ensure_connection():
                    self._log_error("Failed to establish connection for consuming messages")
                    time.sleep(5)  # Wait before retrying
                    continue

                # Declare queue with consistent settings based on use_ttl flag
                # All queues should be durable=True
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
                    self.channel.queue_declare(queue=self.queue, durable=True)

                self.channel.basic_consume(
                    queue=self.queue,
                    on_message_callback=message_callback_wrapper,
                    auto_ack=False  # Manual acknowledgment for better reliability
                )
                self._log_info("Listening for messages on {}. To exit press CTRL+C".format(self.queue))

                # Start consuming - this will block until stop() is called or connection fails
                self.channel.start_consuming()

            except (pika.exceptions.AMQPConnectionError,
                    pika.exceptions.ConnectionClosedByBroker,
                    pika.exceptions.StreamLostError,
                    pika.exceptions.IncompatibleProtocolError) as e:
                self._log_error("Connection error during consumption: {}".format(e))
                # Mark connection as invalid
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

            except Exception as e:
                self._log_error("Unexpected error in consume_message: {}".format(e))
                if self._is_running:
                    time.sleep(5)  # Wait before retrying

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

            # Clear references
            self.connection = None
            self.channel = None

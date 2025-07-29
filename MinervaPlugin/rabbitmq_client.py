import json
import time
import pika
import logging
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
        self._log_info("Attempting to connect to {}".format(_queue))
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_SERVER))
        self.channel = self.connection.channel()
        self.queue = _queue
        #
        self._is_running = True  # Fixed: Set to True so consume_message loop will run

    def _log_info(self, message):
        """Log info message only if DEBUG_ENABLED is True"""
        if DEBUG_ENABLED and self.logger is not None:
            self.logger.info(message)

    def _log_error(self, message):
        """Log error message (always logged regardless of debug setting)"""
        if self.logger is not None:
            self.logger.error(message)

    def send_message(self, message):
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

    def reconnect(self):
        # Safely close existing connection if it's still open
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            self._log_error("Error closing connection during reconnect: {}".format(e))

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_SERVER))
        self.channel = self.connection.channel()
        self._log_info("Reconnected to RabbitMQ server.")


    def consume_message(self, callback):
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

        try:
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

            # Start consuming - this will block until stop() is called
            self.channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            self._log_error("Connection lost: {}".format(e))
            # Only attempt reconnect if we're still supposed to be running
            if self._is_running:
                self.reconnect()
        except Exception as e:
            self._log_error("Error in consume_message: {}".format(e))
        finally:
            print("rabbit mq _is_running False")
            self.close()
            print("closing connection")

    def stop_consuming(self):
        """Stop consuming messages and set running flag to False"""
        self._is_running = False
        if self.channel and not self.channel.is_closed:
            try:
                self.channel.stop_consuming()
                self._log_info("Stopped consuming messages")
            except (pika.exceptions.ConnectionWrongStateError, pika.exceptions.ChannelWrongStateError) as e:
                # These exceptions are expected during shutdown when connection is already closed
                self._log_info("Consumer already stopped or connection closed: {}".format(e))
            except Exception as e:
                self._log_error("Error stopping consumer: {}".format(e))

    def close(self):
        """Close the channel and connection"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
        except (pika.exceptions.ConnectionWrongStateError, pika.exceptions.ChannelWrongStateError) as e:
            # These exceptions are expected during shutdown when connection is already closed
            self._log_info("Channel already closed: {}".format(e))
        except Exception as e:
            self._log_error("Error closing channel: {}".format(e))

        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self._log_info("RabbitMQ connection closed")
        except (pika.exceptions.ConnectionWrongStateError, pika.exceptions.ChannelWrongStateError) as e:
            # These exceptions are expected during shutdown when connection is already closed
            self._log_info("Connection already closed: {}".format(e))
        except Exception as e:
            self._log_error("Error closing connection: {}".format(e))

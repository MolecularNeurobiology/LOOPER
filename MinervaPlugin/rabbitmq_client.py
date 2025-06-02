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
    def __init__(self, logger, queue, id = None, use_ttl = False):
        self.logger = logger
        self.id = id
        self.use_ttl = use_ttl  # Flag to determine if TTL should be applied
        _queue = f"{queue}-{id.replace(":", "")}" if id is not None else queue
        self._log_info(f"Attempting to connect to {_queue}")
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_SERVER))
        self.channel = self.connection.channel()
        self.queue = _queue
        #
        self._is_running = False

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
            # Calculate TTL in milliseconds
            ttl_ms = STREAM_MESSAGE_TTL_SECONDS * 1000

            # Declare queue with TTL for streaming data
            # Messages older than TTL will be automatically discarded
            self.channel.queue_declare(
                queue=self.queue,
                durable=True,
                arguments={'x-message-ttl': ttl_ms}
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
            self.channel.queue_declare(
                queue=self.queue,
                durable=True
            )
            # Publish message without TTL
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue,
                body=message
            )

    def reconnect(self):
        self.connection.close()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_SERVER))
        self.channel = self.connection.channel()
        self._log_info("Reconnected to RabbitMQ server.")


    def consume_message(self, callback):
        def message_callback_wrapper(ch, method, properties, body):
            callback(json.loads(body.decode()))

        print("rabbit mq _is_running True")
        while self._is_running:
            try:
                self.channel.queue_declare(queue=self.queue)
                self.channel.basic_consume(queue=self.queue, on_message_callback=message_callback_wrapper)
                self._log_info(f"Listening for messages on {self.queue}. To exit press CTRL+C")
                self.channel.start_consuming()
            except pika.exceptions.AMQPConnectionError as e:
                self._log_error("Connection lost, retrying in 5 seconds...")
                self.reconnect()
                time.sleep(5)
        print("rabbit mq _is_running False")
        self.close()
        print("closing connection")

    def close(self):
        self.channel.close()
        self.connection.close()

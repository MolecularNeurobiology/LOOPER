import json
import time
import pika
import logging
from config import RABBITMQ_SERVER
class RabbitMQClient:
    def __init__(self, logger, queue, id = None):
        self.logger = logger
        self.id = id
        _queue = f"{queue}-{id.replace(":", "")}" if id is not None else queue
        logger.info(f"Attempting to connect to {_queue}")
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_SERVER))
        self.channel = self.connection.channel()
        self.queue = _queue

    def send_message(self, message):
        self.channel.queue_declare(queue=self.queue, durable=True)
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=message)

    def reconnect(self):
        self.connection.close() 
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_SERVER))
        self.channel = self.connection.channel()
        self.logger.info("Reconnected to RabbitMQ server.")


    def consume_message(self, callback):
        def message_callback_wrapper(ch, method, properties, body):
            callback(json.loads(body.decode()))


        while True:
            try:
                self.channel.queue_declare(queue=self.queue)
                self.channel.basic_consume(queue=self.queue, on_message_callback=message_callback_wrapper)
                self.logger.info(f"Listening for messages on {self.queue}. To exit press CTRL+C")
                self.channel.start_consuming()
            except pika.exceptions.AMQPConnectionError as e:
                self.logger.error("Connection lost, retrying in 5 seconds...")
                self.reconnect() 
                time.sleep(5)

    def close(self):
        self.channel.close()
        self.connection.close()


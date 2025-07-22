# Configuration for RabbitMQ
# Use localhost to connect to Docker RabbitMQ instance
RABBITMQ_SERVER = 'localhost'  # Changed from '10.51.158.26' to connect to local Docker instance
RABBITMQ_PORT = 15672  # Management UI port
RABBITMQ_AMQP_PORT = 5672  # AMQP protocol port (used by pika)
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'
PING_QUEUE = 'ping'
COMMAND_QUEUE = 'command_queue'
MINERVA_STREAM_QUEUE = 'minerva_stream'

# Streaming configuration
STREAM_TIMEOUT_SECONDS = 30  # Stop streaming after 30 seconds without stream command
STREAM_HEARTBEAT_INTERVAL = 10  # Frontend sends stream command every 10 seconds
STREAM_MESSAGE_TTL_SECONDS = 30  # Messages expire after 30 seconds

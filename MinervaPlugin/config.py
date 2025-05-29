# Configuration for RabbitMQ
RABBITMQ_SERVER = '192.168.1.75'
RABBITMQ_PORT = 15672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'
PING_QUEUE = 'ping'
COMMAND_QUEUE = 'command_queue'
MINERVA_STREAM_QUEUE = 'minerva_stream'

# Streaming configuration
STREAM_TIMEOUT_SECONDS = 30  # Stop streaming after 30 seconds without stream command
STREAM_HEARTBEAT_INTERVAL = 10  # Frontend sends stream command every 10 seconds
STREAM_MESSAGE_TTL_SECONDS = 30  # Messages expire after 30 seconds

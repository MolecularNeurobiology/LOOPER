# Configuration for RabbitMQ
# Use localhost to connect to Docker RabbitMQ instance
RABBITMQ_SERVER = (
    "localhost"  # Connect to local Docker instance
)
RABBITMQ_PORT = 15672  # Management UI port
RABBITMQ_AMQP_PORT = 5672  # AMQP protocol port (used by pika)
RABBITMQ_USER = "guest"
RABBITMQ_PASSWORD = "guest"
PING_QUEUE = "ping"
COMMAND_QUEUE = "command_queue"

# Dual queue architecture queue types
STREAM_CONTROL_QUEUE = "stream_control"
RIG_STREAM_QUEUE = "rig_stream"


# Streaming configuration
STREAM_TIMEOUT_SECONDS = 30  # Stop streaming after 30 seconds without stream command
STREAM_HEARTBEAT_INTERVAL = 10  # Frontend sends stream command every 10 seconds
STREAM_MESSAGE_TTL_SECONDS = 30  # Messages expire after 30 seconds

# Dual queue architecture timing configurations
STREAM_USER_TIMEOUT = 60        # seconds - Remove users after this timeout (increased for reliability)
STREAM_CONTROL_TTL = 10         # seconds - TTL for stream control messages


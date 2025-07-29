import time
import json
import threading
import sys

try:
    from command import (
        COMMANDS,
        GoToNextStep,
        StartCommand,
        StreamCommand,
        StopStreamCommand,
    )
except:
    print("attempting relative import of command")
    from .command import (
        COMMANDS,
        GoToNextStep,
        StartCommand,
        StreamCommand,
        StopStreamCommand,
    )
try:
    from rabbitmq_client import RabbitMQClient
except:
    print("attempting relative import of rabbitmqclient")
    from .rabbitmq_client import RabbitMQClient
try:
    from config import (
        PING_QUEUE,
        COMMAND_QUEUE,
        STREAM_CONTROL_QUEUE,
        RIG_STREAM_QUEUE,
        STREAM_USER_TIMEOUT,
        STREAM_CONTROL_TTL,
    )
except:
    print("attempting relative import of config")
    from .config import (
        PING_QUEUE,
        COMMAND_QUEUE,
        STREAM_CONTROL_QUEUE,
        RIG_STREAM_QUEUE,
        STREAM_USER_TIMEOUT,
        STREAM_CONTROL_TTL,
    )
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Union

# Try to import numpy for type checking
try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

PING_INTERVAL = 10
STREAM_INTERVAL = 0.1  # 0.1 seconds interval for streaming data (10 Hz)

# Debug toggle - set to False to disable all debug logs
DEBUG_ENABLED = True


class NumpyJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles numpy types by converting them to native Python types.
    """

    def default(self, obj):
        if HAS_NUMPY:
            # Handle numpy scalar types
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.bool_):
                return bool(obj)

        # Handle regular Python float types (including potential numpy.float64 that might not be caught above)
        if isinstance(obj, float):
            return float(obj)

        # Let the base class default method raise the TypeError
        return super().default(obj)


def safe_json_dumps(obj, **kwargs):
    """
    Safely serialize an object to JSON, handling both regular Python types and numpy types.

    Args:
        obj: The object to serialize
        **kwargs: Additional arguments to pass to json.dumps

    Returns:
        str: JSON string representation of the object
    """
    # Use our custom encoder that handles numpy types
    kwargs.setdefault("cls", NumpyJSONEncoder)
    return json.dumps(obj, **kwargs)


@dataclass
class PluginRegistration:
    mac_address: str


@dataclass
class PingMetrics:
    avg_bpm: int
    avg_hr: int
    step: str
    challengeCount: int
    longestChallenge: str


@dataclass
class MinervaStreamData:
    """
    Class representing the Minerva Stream data payload.
    Uses snake_case field names for backend compatibility with the adapter.
    """

    mac_address: str
    stages: List[Dict[str, Any]] = field(default_factory=list)
    signals: List[Dict[str, Any]] = field(default_factory=list)
    current_stage: Optional[str] = None


@dataclass
class UserStreamSession:
    """
    Class representing a user's streaming session.
    """

    user_id: str
    stream_data: MinervaStreamData
    last_heartbeat: datetime
    rabbit_mq_client: RabbitMQClient
    thread: Optional[threading.Thread] = None
    is_active: bool = True


class Plugin:
    """
    A class representing a plugin that communicates with a remote server via RabbitMQ,
    sending periodic pings and handling incoming commands.
    """

    def __init__(self, registrationParams: PluginRegistration, logger):
        """
        Initializes a Plugin instance with registration parameters and a logger.

        Args:
            registrationParams (PluginRegistration): Registration parameters containing the MAC address.
            logger (object): Logger instance for logging plugin activity.
        """
        self._logger = logger
        self._is_running = False
        self._is_streaming = False
        self._mac_address = registrationParams.mac_address

        # Existing command consumer (for critical commands: start, go_to_next, stop_stream)
        self._rabbit_mq_client_consumer = RabbitMQClient(
            logger, COMMAND_QUEUE, registrationParams.mac_address, use_ttl=False
        )
        self._rabbit_mq_client_producer = RabbitMQClient(
            logger, PING_QUEUE, use_ttl=False
        )

        # Stream control consumer (for stream heartbeat commands - latest-only)
        # Use TTL=True with STREAM_CONTROL_TTL and max_length=1 to match the API's queue configuration
        self._stream_control_consumer = RabbitMQClient(
            logger, STREAM_CONTROL_QUEUE, registrationParams.mac_address, use_ttl=True, ttl_seconds=STREAM_CONTROL_TTL, max_length=1
        )

        # Single rig stream producer (broadcasts to all clients for this rig)
        self._rig_stream_producer = RabbitMQClient(
            logger, RIG_STREAM_QUEUE, registrationParams.mac_address, use_ttl=True
        )

        self._metrics = PingMetrics(
            avg_bpm=0, avg_hr=0, step=None, challengeCount=0, longestChallenge=None
        )

        # Initialize default stream data with MAC address
        self._default_stream_data = MinervaStreamData(mac_address=self._mac_address)

        self._ping_thread = None
        self._ping_lock = threading.Lock()

        self._stream_thread = None
        self._stream_lock = threading.Lock()

        self._command_thread = None
        self._commands_lock = threading.Lock()
        self._commands = []

        # Active users tracking for dual queue architecture
        self._active_users = set()  # Set of active user IDs
        self._last_heartbeat = {}   # Dict mapping user_id -> datetime of last heartbeat
        self._heartbeat_lock = threading.Lock()
        self._stream_control_thread = None
        self._heartbeat_cleanup_thread = None
        self._rig_stream_thread = None

        # Monitoring and observability
        self._start_time = datetime.now()  # Track plugin start time for uptime calculation

    def _ping_server(self):
        with self._ping_lock:
            payload = {
                "mac_address": self._mac_address,
                "timestamp": datetime.now().isoformat(),  # ISO 8601 timestamp
                "avg_hr": self._metrics.avg_hr,
                "step": self._metrics.step,
                **asdict(self._metrics),
            }

            ping_message = safe_json_dumps(payload)

            self._rabbit_mq_client_producer.send_message(ping_message)
            self._log_debug(f"Ping sent to the server. {payload}")



    def _handle_command(self, command):
        """
        Handle critical commands (start, go_to_next, stop_stream) with sequential processing.
        Stream commands are handled separately by _handle_stream_control for latest-only processing.
        """
        self._log_info(f"Plugin {self._mac_address} - Critical command received: {command}")

        if "type" not in command or command["type"] is None:
            self._log_error("Command received with no type")
            return

        try:
            with self._commands_lock:
                command_type = command["type"]
                payload = command.get("payload")
                commandObj = None

                # Handle string command types
                if isinstance(command_type, str):
                    # Map string command types to their enum values (excluding stream commands)
                    string_command_map = {
                        "start": COMMANDS.START.value,
                        "go_to_next": COMMANDS.GO_TO_NEXT_STEP.value,  # Fixed: Frontend sends 'go_to_next'
                        "go_to_next_step": COMMANDS.GO_TO_NEXT_STEP.value,  # Keep backward compatibility
                        "stop_stream": COMMANDS.STOP_STREAM.value,
                        # NOTE: 'stream' commands are NOT handled here - they go to stream control queue
                    }

                    # Try to convert to int first (for backward compatibility)
                    try:
                        command_type = int(command_type)
                    except ValueError:
                        # If not a number, try to map the string to a command value
                        command_type_lower = command_type.lower()

                        # Check if this is a stream command (should be handled by stream control)
                        if command_type_lower == "stream":
                            self._log_warn(f"Stream command received in critical command handler - this should go to stream control queue")
                            return  # Don't process stream commands here

                        if command_type_lower in string_command_map:
                            command_type = string_command_map[command_type_lower]
                        else:
                            # Also check if it matches an enum name (excluding STREAM)
                            try:
                                if command_type.upper() == "STREAM":
                                    self._log_warn(f"Stream command received in critical command handler")
                                    return
                                command_type = COMMANDS[command_type.upper()].value
                            except (KeyError, ValueError):
                                self._log_info(
                                    f"Attempting to process string command type: {command_type}"
                                )

                # Process based on command type (CRITICAL COMMANDS ONLY)
                if command_type == COMMANDS.START.value or command_type == "start":
                    commandObj = StartCommand(payload)
                    self._log_info(f"🚀 START COMMAND: Processing protocol start")
                elif (
                    command_type == COMMANDS.GO_TO_NEXT_STEP.value
                    or command_type == "go_to_next_step"
                    or command_type == "go_to_next"
                ):
                    commandObj = GoToNextStep()
                    self._log_info(f"⏭️ GO_TO_NEXT COMMAND: Advancing to next step")
                elif command_type == COMMANDS.STREAM.value or command_type == "stream":
                    # This should NOT happen - stream commands go to stream control queue
                    self._log_error(f"❌ Stream command received in critical command handler - this is incorrect routing!")
                    self._log_error(f"   Stream commands should be sent to stream_control queue, not command queue")
                    return  # Don't process stream commands in critical command handler
                elif (
                    command_type == COMMANDS.STOP_STREAM.value
                    or command_type == "stop_stream"
                ):
                    # Handle stop streaming command (this is a critical command)
                    commandObj = StopStreamCommand()
                    # Check top level first, then payload
                    user_id = command.get("userId")
                    if user_id is None and payload:
                        user_id = payload.get("userId")
                    if user_id is None:
                        user_id = "default_user"
                    self._log_info(
                        f"🛑 STOP STREAM COMMAND RECEIVED for user: {user_id}"
                    )
                    # Stop streaming for the user
                    self._stop_user_streaming(str(user_id))
                else:
                    self._log_error(f"Unknown critical command type: {command_type}")
                    self._log_error(f"Valid critical commands: start, go_to_next, stop_stream")
                    return

                # Add valid commands to the command queue (if not None)
                if commandObj is not None:
                    self._commands.append(commandObj)
                    self._log_info(f"✅ Critical command processed and stored: {command_type}")
        except Exception as e:
            self._log_error(f"Unknown error occurred processing critical command {str(command)}: {e}")



    def _listen_for_commands(self):
        # added passthrough of _is_running to help with stopping on exit
        self._log_info(f"Starting command listener for MAC: {self._mac_address}")
        self._rabbit_mq_client_consumer.consume_message(self._handle_command)
        self._log_info(f"Command listener stopped for MAC: {self._mac_address}")

    def _ping_loop(self):
        while self._is_running:
            self._ping_server()
            time.sleep(PING_INTERVAL)



    def _stop_user_streaming(self, user_id: str):
        """
        Stops streaming for a specific user.

        Args:
            user_id (str): The user ID to stop streaming for.
        """
        # Remove from active users
        self._stop_user_from_active_set(user_id)
        self._log_info(f"✅ STREAMING STOPPED for user {user_id}")

    def _log_info(self, message):
        """Log info message only if DEBUG_ENABLED is True"""
        if DEBUG_ENABLED and self._logger is not None:
            self._logger.info(message)

    def _log_error(self, message):
        """Log error message (always logged regardless of debug setting)"""
        if self._logger is not None:
            self._logger.error(message)

    def _log_debug(self, message):
        """Log debug message only if DEBUG_ENABLED is True"""
        if DEBUG_ENABLED and self._logger is not None:
            self._logger.debug(f"[DEBUG] {message}")

    def _log_warn(self, message):
        """Log warning message (always logged regardless of debug setting)"""
        if self._logger is not None:
            self._logger.warning(message)

    def stop(self):
        """
        Stops the plugin by terminating its threads and ensuring proper cleanup.

        This method stops the ping loop, command listening thread, and all user streaming sessions.
        """

        print("MP STOP ATTEMPTED")
        self._is_running = False

        # Stop RabbitMQ consumers
        if self._rabbit_mq_client_consumer:
            print("Stopping RabbitMQ command consumer")
            self._rabbit_mq_client_consumer.stop_consuming()
            self._log_info("RabbitMQ command consumer stopped.")

        # Stop stream control consumer
        if self._stream_control_consumer:
            print("Stopping RabbitMQ stream control consumer")
            self._stream_control_consumer.stop_consuming()
            self._log_info("RabbitMQ stream control consumer stopped.")

        # Give a brief moment for the consumer threads to finish processing
        import time
        time.sleep(0.1)

        # Stop all active users
        print("Checking Active Users")
        with self._heartbeat_lock:
            user_ids = list(self._active_users)
        print(f"Active users - {user_ids}")
        for user_id in user_ids:
            print(f"Stopping user stream for {user_id}")
            self._stop_user_streaming(user_id)

        print("Checking for Ping Thread")
        if self._ping_thread:
            print("Stopping Ping Thread")
            self._ping_thread.join(timeout=5)
            self._log_info("Ping thread stopped.")

        print("Checking for Command Thread")
        if self._command_thread:
            print("Stopping Command Listening Thread")
            self._command_thread.join(timeout=5)
            self._log_info("Command listening thread stopped.")

        # Stop stream control thread
        print("Checking for Stream Control Thread")
        if self._stream_control_thread:
            print("Stopping Stream Control Thread")
            self._stream_control_thread.join(timeout=5)
            self._log_info("Stream control thread stopped.")

        # Stop heartbeat cleanup thread
        print("Checking for Heartbeat Cleanup Thread")
        if self._heartbeat_cleanup_thread:
            print("Stopping Heartbeat Cleanup Thread")
            self._heartbeat_cleanup_thread.join(timeout=5)
            self._log_info("Heartbeat cleanup thread stopped.")

        # Stop rig stream thread
        print("Checking for Rig Stream Thread")
        if self._rig_stream_thread:
            print("Stopping Rig Stream Thread")
            self._rig_stream_thread.join(timeout=5)
            self._log_info("Rig stream thread stopped.")

    def start(self):
        """
        Starts the plugin by initializing threads for pinging, session cleanup, and listening for commands.

        This method sets the `is_running` flag to True and starts the necessary threads.
        """
        if not self._is_running:
            self._is_running = True

            # Start the ping loop in a separate thread
            self._ping_thread = threading.Thread(target=self._ping_loop)
            self._ping_thread.daemon = True
            self._ping_thread.start()
            self._log_info("🔧 Plugin started with pinging thread.")



            # Start listening for commands in a separate thread
            self._command_thread = threading.Thread(target=self._listen_for_commands)
            self._command_thread.daemon = True
            self._command_thread.start()
            self._log_info(
                "👂 Command listening thread started - READY TO RECEIVE STREAM COMMANDS"
            )

            # Start the stream control consumer for heartbeat commands
            self._start_stream_control_consumer()

            # Start the heartbeat cleanup thread
            self._start_heartbeat_cleanup_thread()

            # Start the rig stream producer thread
            self._rig_stream_thread = threading.Thread(target=self._stream_data_to_rig_queue)
            self._rig_stream_thread.daemon = True
            self._rig_stream_thread.start()
            self._log_info("📡 Rig stream producer thread started")

    def pop_commands(self):
        """
        Thread-safe method to retrieve and clear the list of commands.

        Returns:
            List[object]: A list of commands received since the last call.
        """
        with self._commands_lock:
            commands_to_return = list(self._commands)  #

            self._commands = list()
            return commands_to_return

    def update_metrics(self, metrics):
        """
        Updates the current metrics used for pings.

        Args:
            metrics (PingMetrics): The new metrics to be stored.
        """
        with self._ping_lock:
            self._metrics = metrics

    def get_metrics(self):
        """
        Retrieves the current metrics used for pings.

        Returns:
            PingMetrics: The current metrics.
        """
        with self._ping_lock:
            return self._metrics

    def update_stream_data(self, stream_data, user_id: str = None):
        """
        Updates the stream data for the rig.

        Args:
            stream_data (MinervaStreamData): The new stream data.
            user_id (str, optional): The user ID (ignored - single stream per rig).
        """
        # Single stream per rig - store as default stream data
        self._default_stream_data = stream_data
        self._log_debug(f"Stream data updated for rig {self._mac_address}")

    def get_stream_data(self, user_id: str = None):
        """
        Retrieves the current stream data for the rig.

        Args:
            user_id (str, optional): The user ID (ignored - single stream per rig).

        Returns:
            MinervaStreamData: The current stream data for the rig.
        """
        # Return the single rig stream data
        return self._default_stream_data

    def set_step(self, step):
        """
        Updates the current step in the metrics and stream data.

        Args:
            step (str): The new step value.
        """
        with self._ping_lock:
            self._metrics.step = step

        # Update the current_stage in the stream data
        if hasattr(self, '_default_stream_data') and self._default_stream_data:
            self._default_stream_data.current_stage = step
            self._log_debug(f"Updated current stage to {step} for rig {self._mac_address}")

    def get_is_running(self):
        """
        Retrieves the current is_running flag

        Returns:
            boolean
        """
        return self._is_running

    def get_active_user_sessions(self):
        """
        Retrieves the list of active user streaming sessions.

        Returns:
            List[str]: List of user IDs with active streaming sessions.
        """
        return self.get_active_users_list()

    def get_user_session_count(self):
        """
        Retrieves the number of active user streaming sessions.

        Returns:
            int: Number of active streaming sessions.
        """
        return self.get_active_users_count()

    def is_user_streaming(self, user_id: str):
        """
        Checks if a specific user has an active streaming session.

        Args:
            user_id (str): The user ID to check.

        Returns:
            bool: True if the user has an active streaming session, False otherwise.
        """
        with self._heartbeat_lock:
            return str(user_id) in self._active_users

    def get_is_streaming(self):
        """
        Checks if there are any active streaming sessions.

        Returns:
            bool: True if there are any active streaming sessions, False otherwise.
        """
        return self.has_active_users()

    # DUAL QUEUE ARCHITECTURE METHODS

    def _start_stream_control_consumer(self):
        """Start the stream control consumer thread for handling heartbeat commands."""
        def stream_control_loop():
            self._log_info(f"Starting stream control listener for MAC: {self._mac_address}")
            self._stream_control_consumer.consume_message(self._handle_stream_control)
            self._log_info(f"Stream control listener stopped for MAC: {self._mac_address}")

        self._stream_control_thread = threading.Thread(target=stream_control_loop)
        self._stream_control_thread.daemon = True
        self._stream_control_thread.start()
        self._log_info("🔄 Started stream control consumer thread")

    def _handle_stream_control(self, command):
        """
        Handle stream control commands (heartbeats) with latest-only processing.
        This method processes stream commands that should NOT block critical commands.

        Args:
            command (dict): The stream control command containing user heartbeat info.
        """
        if command.get('type') == 'stream':
            user_id = command.get('userId')
            if user_id:
                with self._heartbeat_lock:
                    self._active_users.add(str(user_id))
                    self._last_heartbeat[str(user_id)] = datetime.now()
                    self._log_info(f"💓 Stream heartbeat from user {user_id}")
                    self._log_info(f"📡 User {user_id} added to active streaming set")

            else:
                self._log_error("Stream command received without userId")
        else:
            self._log_error(f"Unexpected command type in stream control: {command.get('type')}")

    def _cleanup_inactive_users(self):
        """Remove users who haven't sent heartbeats recently."""
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=STREAM_USER_TIMEOUT)

        with self._heartbeat_lock:
            inactive_users = [
                user_id for user_id, last_beat in self._last_heartbeat.items()
                if current_time - last_beat > timeout_threshold
            ]

            for user_id in inactive_users:
                self._active_users.discard(user_id)
                del self._last_heartbeat[user_id]
                self._log_info(f"🧹 Removed inactive user {user_id} (timeout)")

    def _start_heartbeat_cleanup_thread(self):
        """Start the thread that periodically cleans up inactive users."""
        def cleanup_loop():
            while self._is_running:
                self._cleanup_inactive_users()
                time.sleep(10)  # Check every 10 seconds

        self._heartbeat_cleanup_thread = threading.Thread(target=cleanup_loop)
        self._heartbeat_cleanup_thread.daemon = True
        self._heartbeat_cleanup_thread.start()
        self._log_info("🧹 Started heartbeat cleanup thread")

    def get_active_users_count(self):
        """
        Get the number of active users.

        Returns:
            int: Number of users with recent heartbeats.
        """
        with self._heartbeat_lock:
            return len(self._active_users)

    def get_active_users_list(self):
        """
        Get the list of active user IDs.

        Returns:
            List[str]: List of user IDs with recent heartbeats.
        """
        with self._heartbeat_lock:
            return list(self._active_users)

    def has_active_users(self):
        """
        Check if there are any active users.

        Returns:
            bool: True if there are users with recent heartbeats.
        """
        with self._heartbeat_lock:
            return len(self._active_users) > 0

    def _stop_user_from_active_set(self, user_id: str):
        """
        Remove a user from the active users set.

        Args:
            user_id (str): The user ID to remove from active streaming.
        """
        with self._heartbeat_lock:
            if user_id in self._active_users:
                self._active_users.discard(user_id)
                if user_id in self._last_heartbeat:
                    del self._last_heartbeat[user_id]
                self._log_info(f"🛑 Removed user {user_id} from active streaming set")
            else:
                self._log_info(f"User {user_id} was not in active streaming set")

    def _stream_data_to_rig_queue(self):
        """
        Stream data to the single rig-specific queue when users are active.
        Uses a single broadcast stream instead of per-user streaming.
        """
        while self._is_running:
            # Only stream if there are active users
            if self.has_active_users():
                try:
                    # Generate current stream data
                    stream_data = self._generate_current_stream_data()
                    stream_message = safe_json_dumps(stream_data)

                    # Send to the single rig stream queue
                    self._rig_stream_producer.send_message(stream_message)

                    # Log active user count periodically (every 25 iterations = ~5 seconds)
                    if hasattr(self, '_stream_log_counter'):
                        self._stream_log_counter += 1
                    else:
                        self._stream_log_counter = 1

                    if self._stream_log_counter % 25 == 0:
                        active_count = self.get_active_users_count()
                        self._log_info(f"📡 Streaming to rig queue for {active_count} active users")

                except Exception as e:
                    self._log_error(f"Error streaming to rig queue: {e}")

            time.sleep(0.2)  # 5 times per second

    def _generate_current_stream_data(self):
        """
        Generate the current stream data payload.

        Returns:
            dict: Stream data payload for the current rig state.
        """
        # Use the existing default stream data and update with current metrics
        stream_data = MinervaStreamData(mac_address=self._mac_address)

        # Add current signals (ECG, airflow, BPM, etc.)
        current_signals = self._generate_mock_signals()
        stream_data.signals = current_signals

        # Add current stage information if available
        if hasattr(self, '_current_stage'):
            stream_data.current_stage = self._current_stage

        # Convert to dict for JSON serialization
        return asdict(stream_data)

    def _generate_mock_signals(self):
        """
        Generate mock signal data for streaming.

        Returns:
            List[Dict]: List of signal dictionaries with current data.
        """
        import math
        import random

        current_time = time.time()
        if not hasattr(self, '_signal_start_time'):
            self._signal_start_time = current_time

        elapsed_time = current_time - self._signal_start_time

        signals = [
            {
                'name': 'ECG',
                'type': 'time_series',
                'x_unit': 's',
                'y_unit': 'mV',
                'x_window_min_in_seconds': -10,
                'x_window_max_in_seconds': 0,
                'y_window_min_in_seconds': -1,
                'y_window_max_in_seconds': 1,
                'data': self._generate_ecg_data(elapsed_time)
            },
            {
                'name': 'BPM',
                'type': 'timestamp',
                'display_with': 'ECG',
                'data': self._generate_bpm_events(elapsed_time)
            },
            {
                'name': 'Airflow',
                'type': 'time_series',
                'x_unit': 's',
                'y_unit': 'L/min',
                'x_window_min_in_seconds': -60,
                'x_window_max_in_seconds': 0,
                'y_window_min_in_seconds': -20,
                'y_window_max_in_seconds': 20,
                'data': self._generate_airflow_data(elapsed_time)
            },
            {
                'name': 'avgHR',
                'type': 'single_value',
                'value_unit': 'bpm',
                'data': self._generate_heart_rate(elapsed_time)
            },
            {
                'name': 'Status',
                'type': 'status',
                'data': True
            },
            {
                'name': 'Debug Info',
                'type': 'debug',
                'data': f'Streaming to {self.get_active_users_count()} users'
            }
        ]

        return signals

    def _generate_ecg_data(self, elapsed_time):
        """Generate ECG-like time series data."""
        import math
        import random

        data = []
        # Generate last 10 seconds of ECG data
        for i in range(50):  # 5 Hz sampling
            x = -i * 0.2  # 0.2 second intervals
            time_point = elapsed_time + x

            # Base ECG waveform
            base_ecg = math.sin(time_point * 2) * 0.1

            # Add periodic heart beat spikes
            heart_period = 0.8 + 0.4 * math.sin(time_point * 0.1)
            spike_phase = (time_point % heart_period) / heart_period

            if spike_phase < 0.1:
                spike = 0.8 * math.sin(spike_phase * 10 * math.pi)
            else:
                spike = 0

            # Add noise
            noise = random.gauss(0, 0.02)
            y = base_ecg + spike + noise

            data.append({'x': x, 'y': y})

        return data

    def _generate_airflow_data(self, elapsed_time):
        """Generate airflow time series data."""
        import math
        import random

        data = []
        # Generate last 60 seconds of airflow data
        for i in range(300):  # 5 Hz sampling
            x = -i * 0.2  # 0.2 second intervals
            time_point = elapsed_time + x

            # Breathing cycle (15 breaths per minute)
            breathing_period = 4  # 60/15 = 4 seconds per breath
            airflow = 15 * math.sin(2 * math.pi * time_point / breathing_period)

            # Add minimal noise
            noise = random.gauss(0, 0.5)
            y = airflow + noise

            data.append({'x': x, 'y': y})

        return data

    def _generate_bpm_events(self, elapsed_time):
        """Generate BPM timestamp events."""
        # Generate a few recent BPM events
        events = []
        for i in range(5):  # Last 5 heartbeats
            x = -i * 0.8  # Roughly every 0.8 seconds
            bpm = self._generate_heart_rate(elapsed_time + x)
            events.append({
                'x': x,
                'y': 1,  # Fixed y value for timestamp events
                'label': f'{int(bpm)} BPM'
            })

        return events

    def _generate_heart_rate(self, elapsed_time):
        """Generate realistic heart rate value."""
        import math
        import random

        # Base heart rate with slow trending and noise
        base_hr = 72
        trend = math.sin(elapsed_time * 0.01) * 10  # Slow trend
        noise = random.gauss(0, 3)  # Random variation

        heart_rate = base_hr + trend + noise
        return max(50, min(150, round(heart_rate, 1)))

    # DUAL QUEUE ARCHITECTURE UTILITY METHODS

    def get_command_processing_stats(self):
        """
        Get statistics about command processing for monitoring.

        Returns:
            dict: Statistics about critical vs stream command processing.
        """
        with self._heartbeat_lock:
            active_users_count = len(self._active_users)
            active_users_list = list(self._active_users)

        with self._commands_lock:
            pending_commands_count = len(self._commands)

        return {
            'active_users': active_users_count,
            'active_users_list': active_users_list,
            'pending_critical_commands': pending_commands_count,
            'is_streaming': active_users_count > 0,
            'architecture_mode': 'dual_queue_pure'
        }

    def is_dual_queue_mode(self):
        """
        Check if the plugin is running in dual queue mode.

        Returns:
            bool: True if dual queue architecture is active.
        """
        return (hasattr(self, '_stream_control_consumer') and
                hasattr(self, '_rig_stream_producer') and
                hasattr(self, '_active_users'))

    def get_streaming_metrics(self):
        """
        Get comprehensive streaming metrics for monitoring and observability.

        Returns:
            dict: Detailed streaming metrics including user activity and system health.
        """
        with self._heartbeat_lock:
            active_users_count = len(self._active_users)
            user_list = list(self._active_users)
            last_heartbeats = {
                user: beat.isoformat() if beat else None
                for user, beat in self._last_heartbeat.items()
            }

        with self._commands_lock:
            pending_commands = len(self._commands)

        with self._ping_lock:
            current_step = getattr(self._metrics, 'step', 'unknown')

        # Calculate uptime
        uptime_seconds = (datetime.now() - self._start_time).total_seconds() if hasattr(self, '_start_time') else 0

        # Get thread status
        thread_status = {
            'command_thread': self._command_thread.is_alive() if self._command_thread else False,
            'stream_control_thread': self._stream_control_thread.is_alive() if self._stream_control_thread else False,
            'heartbeat_cleanup_thread': self._heartbeat_cleanup_thread.is_alive() if self._heartbeat_cleanup_thread else False,
            'rig_stream_thread': self._rig_stream_thread.is_alive() if self._rig_stream_thread else False,
        }

        return {
            'timestamp': datetime.now().isoformat(),
            'mac_address': self._mac_address,
            'architecture_mode': 'dual_queue_pure',
            'active_users': {
                'count': active_users_count,
                'user_list': user_list,
                'last_heartbeats': last_heartbeats
            },
            'commands': {
                'pending_critical': pending_commands,
                'processing_enabled': True
            },
            'streaming': {
                'is_active': active_users_count > 0,
                'current_step': current_step,
                'stream_data_available': self._default_stream_data is not None
            },
            'system': {
                'uptime_seconds': uptime_seconds,
                'threads': thread_status
            },
            'queues': {
                'command_queue': f"command_queue-{self._mac_address.replace(':', '')}",
                'stream_control_queue': f"stream_control-{self._mac_address.replace(':', '')}",
                'rig_stream_queue': f"rig_stream-{self._mac_address.replace(':', '')}"
            }
        }

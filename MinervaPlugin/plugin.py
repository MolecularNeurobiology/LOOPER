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
        MINERVA_STREAM_QUEUE,
        STREAM_TIMEOUT_SECONDS,
    )
except:
    print("attempting relative import of config")
    from .config import (
        PING_QUEUE,
        COMMAND_QUEUE,
        MINERVA_STREAM_QUEUE,
        STREAM_TIMEOUT_SECONDS,
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
        self._rabbit_mq_client_consumer = RabbitMQClient(
            logger, COMMAND_QUEUE, registrationParams.mac_address, use_ttl=False
        )
        self._rabbit_mq_client_producer = RabbitMQClient(
            logger, PING_QUEUE, use_ttl=False
        )
        # Create a new RabbitMQ client for streaming data
        self._rabbit_mq_client_stream = RabbitMQClient(logger, MINERVA_STREAM_QUEUE)

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

        # User streaming sessions management
        self._user_sessions: Dict[str, UserStreamSession] = {}
        self._sessions_lock = threading.Lock()
        self._session_cleanup_thread = None

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

    def _stream_data_to_server(self, session: UserStreamSession):
        """
        Sends stream data to the server for a specific user session.

        Args:
            session (UserStreamSession): The user session to stream data for.
        """
        try:
            # Make sure stream_data is updated with the current MAC address
            session.stream_data.mac_address = self._mac_address

            # !!! changed from info to debug level, info level floods the status window of the local gui and overworks the client, also just commenting out since use is primarily for debug testing of signal sending
            # Debug: Log airflow signal data before serialization
            """
            airflow_signal = next(
                (s for s in session.stream_data.signals if s.get("name") == "Airflow"),
                None,
            )
            if airflow_signal and airflow_signal.get("data"):
                self._log_debug(
                    f"Airflow signal before serialization: name={airflow_signal['name']}, type={airflow_signal['type']}, data_points={len(airflow_signal['data'])}"
                )
            """
            # Convert stream data to JSON using safe serialization
            stream_message = safe_json_dumps(asdict(session.stream_data))

            # Debug: Check if airflow data is in the serialized message
            """
            if '"Airflow"' in stream_message:
                self._log_debug(
                    f"✓ Airflow signal found in serialized message for user {session.user_id}"
                )
            else:
                self._log_debug(
                    f"✗ Airflow signal NOT found in serialized message for user {session.user_id}"
                )
            """

            # Send the stream data to the server
            session.rabbit_mq_client.send_message(stream_message)
            """
            self._log_debug(
                f"Stream data sent to server for user {session.user_id}, MAC {session.stream_data.mac_address}"
            )
            """
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            self._log_error(
                f"Error streaming data for user {session.user_id}: {e} \n {lineno}"
            )

    def _handle_command(self, command):
        self._log_info(f"Plugin {self._mac_address} - Command received: {command}")

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
                    # Map string command types to their enum values
                    string_command_map = {
                        "start": COMMANDS.START.value,
                        "go_to_next": COMMANDS.GO_TO_NEXT_STEP.value,  # Fixed: Frontend sends 'go_to_next'
                        "go_to_next_step": COMMANDS.GO_TO_NEXT_STEP.value,  # Keep backward compatibility
                        "stream": COMMANDS.STREAM.value,
                        "stop_stream": COMMANDS.STOP_STREAM.value,
                        # Add other command mappings as needed
                    }

                    # Try to convert to int first (for backward compatibility)
                    try:
                        command_type = int(command_type)
                    except ValueError:
                        # If not a number, try to map the string to a command value
                        command_type_lower = command_type.lower()
                        if command_type_lower in string_command_map:
                            command_type = string_command_map[command_type_lower]
                        else:
                            # Also check if it matches an enum name
                            try:
                                command_type = COMMANDS[command_type.upper()].value
                            except (KeyError, ValueError):
                                self._log_info(
                                    f"Attempting to process string command type: {command_type}"
                                )

                # Process based on command type
                if command_type == COMMANDS.START.value or command_type == "start":
                    commandObj = StartCommand(payload)
                elif (
                    command_type == COMMANDS.GO_TO_NEXT_STEP.value
                    or command_type == "go_to_next_step"
                    or command_type == "go_to_next"
                ):
                    commandObj = GoToNextStep()
                elif command_type == COMMANDS.STREAM.value or command_type == "stream":
                    # Handle the stream command - pass the full command to get userId from top level
                    commandObj = StreamCommand(command)
                    user_id = commandObj.get_user_id()
                    self._log_info(
                        f"🚀 STREAM COMMAND RECEIVED: userId={user_id}, command={command}"
                    )
                    # Start or update user streaming session
                    self._handle_user_stream_command(user_id, payload)
                elif (
                    command_type == COMMANDS.STOP_STREAM.value
                    or command_type == "stop_stream"
                ):
                    # Handle stop streaming command
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
                    self._stop_user_streaming(str(user_id))
                else:
                    self._log_error(f"Unknown command type: {command_type}")
                    return

                # Add valid commands to the command queue (if not None)
                if commandObj is not None:
                    self._commands.append(commandObj)
                    self._log_info(f"Received and stored command: {command}")
        except Exception as e:
            self._log_error(f"Unknown error occurred with {str(command)}: {e}")

    def _handle_user_stream_command(self, user_id: str, payload: Dict[str, Any]):
        """
        Handles a stream command for a specific user.

        Args:
            user_id (str): The user ID for the streaming session.
            payload (dict): The payload containing the stream data.
        """
        with self._sessions_lock:
            current_time = datetime.now()

            if user_id in self._user_sessions:
                # Update existing session
                session = self._user_sessions[user_id]
                session.last_heartbeat = current_time
                self._update_session_stream_data(session, payload)
                self._log_info(
                    f"📡 Updated existing streaming session for user {user_id}"
                )
            else:
                # Create new session
                self._create_user_session(user_id, payload, current_time)
                self._log_info(
                    f"🎯 Created NEW streaming session for user {user_id} - STREAMING NOW ACTIVE!"
                )

    def _create_user_session(
        self, user_id: str, payload: Dict[str, Any], current_time: datetime
    ):
        """
        Creates a new user streaming session.

        Args:
            user_id (str): The user ID for the streaming session.
            payload (dict): The payload containing the stream data.
            current_time (datetime): The current timestamp.
        """
        # Create stream data for this user
        stream_data = MinervaStreamData(mac_address=self._mac_address)
        self._update_stream_data_from_payload(stream_data, payload)

        # Create rig-specific user queue (format: minerva_stream_{macAddress}_{userId})
        mac_clean = self._mac_address.replace(":", "")
        user_queue = f"{MINERVA_STREAM_QUEUE}_{mac_clean}_{user_id}"
        self._log_info(
            f"Creating user session for user {user_id} with rig-specific queue: {user_queue}"
        )
        rabbit_client = RabbitMQClient(self._logger, user_queue, use_ttl=True)

        # Create session
        session = UserStreamSession(
            user_id=user_id,
            stream_data=stream_data,
            last_heartbeat=current_time,
            rabbit_mq_client=rabbit_client,
            is_active=True,
        )

        # Start streaming thread for this user
        session.thread = threading.Thread(
            target=self._user_stream_loop, args=(session,)
        )
        session.thread.daemon = True
        session.thread.start()
        self._log_info(
            f"🔄 Started streaming thread for user {user_id} on queue: {user_queue}"
        )

        self._user_sessions[user_id] = session

    def _update_session_stream_data(
        self, session: UserStreamSession, payload: Dict[str, Any]
    ):
        """
        Updates the stream data for a user session.

        Args:
            session (UserStreamSession): The user session to update.
            payload (dict): The payload containing the stream data.
        """
        self._update_stream_data_from_payload(session.stream_data, payload)

    def _update_stream_data_from_payload(
        self, stream_data: MinervaStreamData, payload: Dict[str, Any]
    ):
        """
        Updates stream data from a command payload.

        Args:
            stream_data (MinervaStreamData): The stream data to update.
            payload (dict): The payload containing the stream data.
        """
        if payload.get("macAddress"):
            stream_data.mac_address = payload.get("macAddress")

        if payload.get("stages"):
            stream_data.stages = payload.get("stages")

        if payload.get("signals"):
            stream_data.signals = payload.get("signals")

        if payload.get("currentStage"):
            stream_data.current_stage = payload.get("currentStage")

    def _listen_for_commands(self):
        # added passthrough of _is_running to help with stopping on exit
        self._log_info(f"Starting command listener for MAC: {self._mac_address}")
        self._rabbit_mq_client_consumer.consume_message(self._handle_command)
        self._log_info(f"Command listener stopped for MAC: {self._mac_address}")

    def _ping_loop(self):
        while self._is_running:
            self._ping_server()
            time.sleep(PING_INTERVAL)

    def _user_stream_loop(self, session: UserStreamSession):
        """
        Continuously streams data for a specific user session.

        Args:
            session (UserStreamSession): The user session to stream data for.
        """
        self._log_info(f"Starting stream loop for user {session.user_id}")

        while self._is_running and session.is_active:
            try:
                self._stream_data_to_server(session)
            except Exception as e:
                self._log_error(f"Error streaming data for user {session.user_id}: {e}")
            time.sleep(STREAM_INTERVAL)

        self._log_info(f"Streaming stopped for user {session.user_id}")

    def _stop_user_streaming(self, user_id: str):
        """
        Stops streaming for a specific user.

        Args:
            user_id (str): The user ID to stop streaming for.
        """

        with self._sessions_lock:

            if user_id in self._user_sessions:
                session = self._user_sessions[user_id]
                session.is_active = False

                # Wait for thread to finish
                if session.thread and session.thread.is_alive():
                    session.thread.join(timeout=5)
                # Close RabbitMQ connection
                try:
                    session.rabbit_mq_client.close()
                except Exception as e:
                    self._log_error(
                        f"Error closing RabbitMQ client for user {user_id}: {e}"
                    )

                # Remove session
                del self._user_sessions[user_id]
                self._log_info(f"✅ STREAMING STOPPED for user {user_id}")
            else:
                self._log_info(
                    f"⚠️ No active streaming session found for user {user_id}"
                )

    def _session_cleanup_loop(self):
        """
        Periodically checks for and cleans up inactive user sessions.
        """
        while self._is_running:
            current_time = datetime.now()
            timeout_threshold = timedelta(seconds=STREAM_TIMEOUT_SECONDS)

            with self._sessions_lock:
                users_to_remove = []
                for user_id, session in self._user_sessions.items():
                    if current_time - session.last_heartbeat > timeout_threshold:
                        users_to_remove.append(user_id)

                # Remove timed-out sessions
                for user_id in users_to_remove:
                    self._log_info(
                        f"Session timeout for user {user_id}, cleaning up..."
                    )
                    self._stop_user_streaming(user_id)

            time.sleep(PING_INTERVAL)  # Check every ping interval

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

        # Stop RabbitMQ consumer first
        if self._rabbit_mq_client_consumer:
            print("Stopping RabbitMQ consumer")
            self._rabbit_mq_client_consumer.stop_consuming()
            self._log_info("RabbitMQ consumer stopped.")

        # Stop all user streaming sessions
        print("Checking Sessions")
        # with self._sessions_lock: # <-- removed this, self._stop_user_streaming also makes a call using with self._sessions_lock ...using it here seems to block it
        print("Sessions found")
        user_ids = list(self._user_sessions.keys())
        print(f"users - {user_ids}")
        for user_id in user_ids:
            print("Stopping user stream")
            self._stop_user_streaming(user_id)

        print("Checking for Ping Thread")
        if self._ping_thread:
            print("Stopping Ping Thread")
            self._ping_thread.join(timeout=5)
            self._log_info("Ping thread stopped.")
        print("Checking for Session Thread")
        if self._session_cleanup_thread:
            print("Running Session Cleanup")
            self._session_cleanup_thread.join(timeout=5)
            self._log_info("Session cleanup thread stopped.")
        print("Checking for Command Thread")
        if self._command_thread:
            print("Stopping Command Listening Thread")
            self._command_thread.join(timeout=5)
            self._log_info("Command listening thread stopped.")

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

            # Start the session cleanup loop in a separate thread
            self._session_cleanup_thread = threading.Thread(
                target=self._session_cleanup_loop
            )
            self._session_cleanup_thread.daemon = True
            self._session_cleanup_thread.start()
            self._log_info("🧹 Session cleanup thread started.")

            # Start listening for commands in a separate thread
            self._command_thread = threading.Thread(target=self._listen_for_commands)
            self._command_thread.daemon = True
            self._command_thread.start()
            self._log_info(
                "👂 Command listening thread started - READY TO RECEIVE STREAM COMMANDS"
            )

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
        Updates the stream data for a specific user or all users.

        Args:
            stream_data (MinervaStreamData): The new stream data.
            user_id (str, optional): The user ID to update. If None, updates default data.
        """
        if user_id:
            with self._sessions_lock:
                if user_id in self._user_sessions:
                    self._user_sessions[user_id].stream_data = stream_data
                    # self._log_debug(f"user_id: {user_id}, stream_data: {stream_data}")
        else:
            # Update default stream data
            self._default_stream_data = stream_data
            # self._log_debug(f"user_id: NA, stream_data: {stream_data}")

    def get_stream_data(self, user_id: str = None):
        """
        Retrieves the current stream data for a user or default data.

        Args:
            user_id (str, optional): The user ID to get data for. If None, returns default data.

        Returns:
            MinervaStreamData: The current stream data.
        """
        if user_id:
            with self._sessions_lock:
                if user_id in self._user_sessions:
                    return self._user_sessions[user_id].stream_data
                return None
        else:
            return self._default_stream_data

    def set_step(self, step):
        """
        Updates the current step in the metrics and all active streaming sessions.

        Args:
            step (str): The new step value.
        """
        with self._ping_lock:
            self._metrics.step = step

        # Also update the current_stage in all active streaming sessions
        with self._sessions_lock:
            for session in self._user_sessions.values():
                session.stream_data.current_stage = step

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
        with self._sessions_lock:
            return list(self._user_sessions.keys())

    def get_user_session_count(self):
        """
        Retrieves the number of active user streaming sessions.

        Returns:
            int: Number of active streaming sessions.
        """
        with self._sessions_lock:
            return len(self._user_sessions)

    def is_user_streaming(self, user_id: str):
        """
        Checks if a specific user has an active streaming session.

        Args:
            user_id (str): The user ID to check.

        Returns:
            bool: True if the user has an active streaming session, False otherwise.
        """
        with self._sessions_lock:
            return (
                user_id in self._user_sessions
                and self._user_sessions[user_id].is_active
            )

    def get_is_streaming(self):
        """
        Checks if there are any active streaming sessions.

        Returns:
            bool: True if there are any active streaming sessions, False otherwise.
        """
        with self._sessions_lock:
            return len(self._user_sessions) > 0

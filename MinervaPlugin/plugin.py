import time
import json
import threading
try: 
    from command import COMMANDS, GoToNextStep, StartCommand, StreamCommand, StopStreamCommand
except:
    print('attempting relative import of command')
    from .command import COMMANDS, GoToNextStep, StartCommand, StreamCommand, StopStreamCommand
try:
    from rabbitmq_client import RabbitMQClient
except:
    print('attempting relative import of rabbitmqclient')
    from .rabbitmq_client import RabbitMQClient
try:
    from config import PING_QUEUE, COMMAND_QUEUE, MINERVA_STREAM_QUEUE
except:
    print('attempting relative import of config')
    from .config import PING_QUEUE, COMMAND_QUEUE, MINERVA_STREAM_QUEUE
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Union

PING_INTERVAL = 10
STREAM_INTERVAL = 2  # 2 seconds interval for streaming data

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
    This matches the TypeScript interface MinervaStreamPayload.
    """
    macAddress: str
    stages: List[Dict[str, Any]] = field(default_factory=list)
    signals: List[Dict[str, Any]] = field(default_factory=list)
    currentStage: Optional[str] = None

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
        self._rabbit_mq_client_consumer = RabbitMQClient(logger, COMMAND_QUEUE, registrationParams.mac_address)
        self._rabbit_mq_client_producer = RabbitMQClient(logger, PING_QUEUE)
        # Create a new RabbitMQ client for streaming data
        self._rabbit_mq_client_stream = RabbitMQClient(logger, MINERVA_STREAM_QUEUE)

        self._metrics = PingMetrics(
            avg_bpm=0,
            avg_hr=0,
            step=None,
            challengeCount=0,
            longestChallenge=None
        )

        # Initialize stream data with MAC address
        self._stream_data = MinervaStreamData(
            macAddress=self._mac_address
        )

        self._ping_thread = None
        self._ping_lock = threading.Lock()

        self._stream_thread = None
        self._stream_lock = threading.Lock()

        self._command_thread = None
        self._commands_lock = threading.Lock()
        self._commands = []
    
    def _ping_server(self):
        with self._ping_lock:
            payload = {
                'mac_address': self._mac_address,
                'timestamp': datetime.now().isoformat(),  # ISO 8601 timestamp
                'avg_hr': self._metrics.avg_hr,
                'step': self._metrics.step,
                **asdict(self._metrics)
            }

            ping_message = json.dumps(payload)

            self._rabbit_mq_client_producer.send_message(ping_message)
            self._log_info(f"Ping sent to the server. {payload}")
    
    def _stream_data_to_server(self):
        """
        Sends stream data to the server using the stream RabbitMQ client.
        """
        with self._stream_lock:
            # Make sure stream_data is updated with the current MAC address
            self._stream_data.macAddress = self._mac_address
            
            # Convert stream data to JSON
            stream_message = json.dumps(asdict(self._stream_data))
            
            # Send the stream data to the server
            self._rabbit_mq_client_stream.send_message(stream_message)
            self._log_info(f"Stream data sent to server for {self._stream_data.macAddress}")
    
    def _handle_command(self, command):
            self._log_info(f"Command received: {command}")
            
            if 'type' not in command or command['type'] is None:
                self._log_error("Command received with no type")
                return

            try:
                with self._commands_lock:
                    command_type = command['type']
                    payload = command.get('payload')
                    commandObj = None
                    
                    # Convert the command type to int if it's a string
                    if isinstance(command_type, str):
                        try:
                            command_type = int(command_type)
                        except ValueError:
                            self._log_error(f"Invalid command type: {command_type}")
                            return
                    
                    # Process based on command type
                    if command_type == COMMANDS.START.value:
                        commandObj = StartCommand(payload)
                    elif command_type == COMMANDS.GO_TO_NEXT_STEP.value:
                        commandObj = GoToNextStep()
                    elif command_type == COMMANDS.STREAM.value:
                        # Handle the stream command
                        commandObj = StreamCommand(payload)
                        # Update stream data with the payload
                        self._update_stream_data(payload)
                        # Start streaming if not already streaming
                        if not self._is_streaming:
                            self._start_streaming()
                    elif command_type == COMMANDS.STOP_STREAM.value:
                        # Handle stop streaming command
                        commandObj = StopStreamCommand()
                        self._stop_streaming()
                    else:
                        self._log_error(f'Unknown command type: {command_type}')
                        return

                    # Add valid commands to the command queue (if not None)
                    if commandObj is not None:
                        self._commands.append(commandObj)
                        self._log_info(f"Received and stored command: {command}")
            except Exception as e:
                self._log_error(f"Unknown error occurred with {str(command)}: {e}")

    def _update_stream_data(self, payload):
        """
        Updates the stream data from the command payload.
        
        Args:
            payload (dict): The payload containing the stream data.
        """
        with self._stream_lock:
            if payload.get('macAddress'):
                # Normally we'd keep the MAC address from initialization,
                # but allow it to be overridden if explicitly specified
                self._stream_data.macAddress = payload.get('macAddress')
            
            if payload.get('stages'):
                self._stream_data.stages = payload.get('stages')
            
            if payload.get('signals'):
                self._stream_data.signals = payload.get('signals')
            
            if payload.get('currentStage'):
                self._stream_data.currentStage = payload.get('currentStage')
            
            self._log_info(f"Stream data updated")

    def _listen_for_commands(self):
        self._rabbit_mq_client_consumer.consume_message(self._handle_command)
    
    def _ping_loop(self):
        while self._is_running:
            self._ping_server()
            time.sleep(PING_INTERVAL)

    def _stream_loop(self):
        """
        Continuously streams data at the specified interval while streaming is enabled.
        """
        self._log_info("Starting stream loop")
        while self._is_running and self._is_streaming:
            try:
                self._stream_data_to_server()
            except Exception as e:
                self._log_error(f"Error streaming data: {e}")
            time.sleep(STREAM_INTERVAL)
        
        self._log_info("Streaming stopped")
    
    def _start_streaming(self):
        """
        Starts the streaming loop in a separate thread.
        """
        if not self._is_streaming:
            self._is_streaming = True
            self._stream_thread = threading.Thread(target=self._stream_loop)
            self._stream_thread.daemon = True  # Make thread daemon so it terminates with the main thread
            self._stream_thread.start()
            self._log_info("Streaming started")

    def _stop_streaming(self):
        """
        Stops the streaming loop.
        """
        if self._is_streaming:
            self._is_streaming = False
            # The thread will terminate when it checks self._is_streaming in the next loop iteration
            self._log_info("Stopping streaming...")

    def _log_info(self, message):
        if self._logger is not None:
            self._logger.info(message)

    def _log_error(self, message):
        if self._logger is not None:
            self._logger.error(message)

    def stop(self):
        """
        Stops the plugin by terminating its threads and ensuring proper cleanup.

        This method stops the ping loop and the command listening thread, ensuring 
        all threads are safely joined.
        """
        self._is_running = False
        self._is_streaming = False  # Also stop streaming
        
        if self._ping_thread:
            self._ping_thread.join(timeout=5)  # Ensure the ping thread finishes (with timeout)
            self._log_info("Ping thread stopped.")
        
        if self._stream_thread:
            self._stream_thread.join(timeout=5)  # Ensure the stream thread finishes (with timeout)
            self._log_info("Stream thread stopped.")
            
        if self._command_thread:
            self._command_thread.join(timeout=5)  # Ensure the command listening thread finishes (with timeout)
            self._log_info("Command listening thread stopped.")
    
    def start(self):
        """
        Starts the plugin by initializing threads for pinging and listening for commands.

        This method sets the `is_running` flag to True and starts the `ping_thread`
        and `command_thread`.
        """
        if not self._is_running:
            self._is_running = True

            # Start the ping loop in a separate thread
            self._ping_thread = threading.Thread(target=self._ping_loop)
            self._ping_thread.daemon = True  # Make thread daemon so it terminates with the main thread
            self._ping_thread.start()
            self._log_info("Plugin started with pinging thread.")

            # Start listening for commands in a separate thread
            self._command_thread = threading.Thread(target=self._listen_for_commands)
            self._command_thread.daemon = True  # Make thread daemon so it terminates with the main thread
            self._command_thread.start()
            self._log_info("Command listening thread started.")

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

    def update_stream_data(self, stream_data):
        """
        Updates the stream data to be sent during streaming.
        
        Args:
            stream_data (MinervaStreamData): The new stream data.
        """
        with self._stream_lock:
            self._stream_data = stream_data

    def get_stream_data(self):
        """
        Retrieves the current stream data.
        
        Returns:
            MinervaStreamData: The current stream data.
        """
        with self._stream_lock:
            return self._stream_data

    def set_step(self, step):
        """
        Updates the current step in the metrics.

        Args:
            step (str): The new step value.
        """
        with self._ping_lock:
            self._metrics.step = step
            
        # Also update the currentStage in stream data if streaming is active
        if self._is_streaming:
            with self._stream_lock:
                self._stream_data.currentStage = step

    def get_is_running(self):
        """
        Retrieves the current is_running flag

        Returns:
            boolean
        """
        return self._is_running
        
    def get_is_streaming(self):
        """
        Retrieves the current is_streaming flag
        
        Returns:
            boolean
        """
        return self._is_streaming
import time
import json
import threading
try: 
    from command import GoToNextStep, StartCommand
except:
    print('attempting relative import of command')
    from .command import GoToNextStep, StartCommand
try:
    from rabbitmq_client import RabbitMQClient
except:
    print('attempting relative import of rabbitmqclient')
    from .rabbitmq_client import RabbitMQClient
try:
    from config import PING_QUEUE, COMMAND_QUEUE
except:
    print('attempting relative import of config')
    from .config import PING_QUEUE, COMMAND_QUEUE
from datetime import datetime
from dataclasses import dataclass, asdict

PING_INTERVAL = 10

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
        self._mac_address = registrationParams.mac_address
        self._rabbit_mq_client_consumer = RabbitMQClient(logger, COMMAND_QUEUE, registrationParams.mac_address)
        self._rabbit_mq_client_producer = RabbitMQClient(logger, PING_QUEUE)

        self._metrics = PingMetrics(
            avg_bpm=0,
            avg_hr=0,
            step=None,
            challengeCount=0,
            longestChallenge=None
        )

        self._ping_thread = None
        self._ping_lock = threading.Lock()

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
    
    def _handle_command(self, command):
            self._log_info(f"Command received: {command}")
            
            if (command['type'] is None):
                self._log_error("Command received with no type")
                return

            try:
                with self._commands_lock:
                    commandObj = None
                    match command['type']:
                        case 'start':
                            commandObj = StartCommand(command['payload'])
                        case 'go_to_next':
                            commandObj = GoToNextStep()
                        case _:
                            commandObj = None

                    if commandObj is None:
                        self._log_error('Unknown command received')
                        return
                        
                    self._commands.append(commandObj)
                    self._log_info(f"Received and stored command: {command}")
            except Exception as e:
                self._log_error(f"Unknown error occurred with {str(command)}: {e}")


    def _listen_for_commands(self):
        # added passthrough of _is_running to help with stopping on exit
        self._rabbit_mq_client_consumer.consume_message(self._handle_command)
    
    def _ping_loop(self):
        while self._is_running:
            self._ping_server()
            time.sleep(PING_INTERVAL)

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
        
        print("MP STOP ATTEMPTED")
        self._is_running = False
        if self._ping_thread:
            print("stopping ping thread")
            self._ping_thread.join()  # Ensure the ping thread finishes
            self._log_info("Ping thread stopped.")
            print("ping thread stopped")
        else: print("no ping thread to stop")
        if self._command_thread:
            print("stopping command thread")
            self._rabbit_mq_client_consumer._is_running = False
            print("rabbitmq is running status changes to False")
            self._command_thread.join()  # Ensure the command listening thread finishes
            self._log_info("Command listening thread stopped.")
            print("command thread stopped")
        else: print ("no command thread to stop")
        print("STOP COMMANDS FINISHED")

    
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
            self._ping_thread.start()
            self._log_info("Plugin started with pinging thread.")

            # Start listening for commands in a separate thread
            self._command_thread = threading.Thread(target=self._listen_for_commands)
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

    def set_step(self, step):
        """
        Updates the current step in the metrics.

        Args:
            step (str): The new step value.
        """
        with self._ping_lock:
            self._metrics.step = step

    def get_is_running(self):
        """
        Retrieves the current is_running flag

        Returns:
            boolean
        """
        return self._is_running

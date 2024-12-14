# Minerva Plugin

The code in this folder provides the PCC program with a way to interface with the minerva command center.

Here is a breakdown of the files and their intent:
- _command.py_ a data transfer object class that represents a command send from the central server to a Pi
- _config.py_ holds rabbitmq configuration settings. The development defaults are submitted to source code
- _fake_mac_addresses.txt_ A list of 50 fake MAC addresses for simulating a RPi. Not needed for use with the PCC program
- _faker.py_ a static class that generates random values for HR and BPM
- _plugin.py_ The main plugin code.
- _rabbitmq_client.py_ The class that handles connecting to the RabbitMQ server
- _requirements.txt_ the pip requirements needed to run the plugin and simulator. Used by the _start.sh_ script
- _rig.py_ A data transfer object class that represents a rig. This is only used by the simulator, the plugin doesnt need it
- _run.py_ A class to keep track of a simulated run. The plugin does not need this
- _simulation.py_ A class that represents a single RPI in the simulator. Not needed by the plugin
- _simulator.py_ The top level class that runs the simulation
- _start.sh_ A bash script to start the simulator
- _step.py_ represents a step in a simulated run. Not used by the plugin.

## Plugin API

### Creating a `Plugin` instance:
The `Plugin` class takes in two arguments:
1. a `PluginRegistration` object
    - Note that currently the only item needed to register the plugin is the device MAC address
2. a logger that has info and error methods

```python
plugin = Plugin(PluginRegistration(mac_address=mac_address), logger)
```

### Using the `Plugin` class
- *stop()* Stops the plugin by terminating its threads and ensuring proper cleanup.
- *start()* Starts the plugin by initializing threads for pinging and listening for commands.
- *pop_commands()* Thread-safe method to retrieve and clear the list of commands.
- *update_metrics()* Updates the current metrics used for pings.
- *get_metrics()* Retrieves the current metrics used for pings.
- *set_step()* Updates the current step in the metrics.
- *get_is_running()* Retrieves the current is_running flag

### Notes for setting up dev/testing environment
- use of the plugin requires a rabbitmq server to connect to
- if not present on your system, or no remote server is available - install rabbitmq and erlang.
# Minerva Plugin API Documentation

The Minerva Plugin provides a comprehensive interface for medical device rigs to communicate with the Minerva command center via RabbitMQ. It implements a dual-queue architecture for efficient command processing and real-time data streaming.

## Overview

The plugin serves as a bridge between physical medical devices (or simulators) and the Minerva system, handling:
- Device registration and heartbeat monitoring
- Command reception and processing
- Real-time data streaming to multiple clients
- Status reporting and error handling
- User session management

## Core Components

### Data Classes

#### `PluginRegistration`
Registration parameters for device identification.
```python
@dataclass
class PluginRegistration:
    mac_address: str  # Unique device identifier
```

#### `PingMetrics`
Operational metrics sent with heartbeat pings.
```python
@dataclass
class PingMetrics:
    avg_bpm: int              # Average beats per minute
    avg_hr: int               # Average heart rate
    step: str                 # Current experiment step
    challengeCount: int       # Number of challenges encountered
    longestChallenge: str     # Description of longest challenge
    statuses: List[Dict]      # Status reports for monitoring
```

#### `MinervaStreamData`
Real-time streaming data payload.
```python
@dataclass
class MinervaStreamData:
    mac_address: str                    # Device identifier
    stages: List[Dict[str, Any]]        # Experiment stages
    signals: List[Dict[str, Any]]       # Signal data (ECG, BPM, etc.)
    current_stage: Optional[str]        # Current experiment stage
```

## Public API

### Plugin Initialization

```python
from plugin import Plugin, PluginRegistration

# Create plugin instance
registration = PluginRegistration(mac_address="AA:BB:CC:DD:EE:FF")
plugin = Plugin(registration, logger)
```

### Core Lifecycle Methods

#### `start()`
Initializes and starts all plugin services.
```python
plugin.start()
```
**Use Case**: Start the plugin when your application begins. This initializes:
- Heartbeat ping system
- Command listening threads
- Stream control consumer
- User session management
- Status reporting system

#### `stop()`
Gracefully shuts down all plugin services.
```python
plugin.stop()
```
**Use Case**: Clean shutdown when your application terminates. Ensures proper cleanup of:
- All active threads
- RabbitMQ connections
- User streaming sessions

#### `get_is_running()`
Check if the plugin is currently active.
```python
is_active = plugin.get_is_running()  # Returns bool
```

### Command Processing

#### `pop_commands()`
Retrieve and clear pending commands (thread-safe).
```python
commands = plugin.pop_commands()  # Returns List[Dict]
for command in commands:
    # Process each command
    command_type = command.get('type')
    # Handle based on command type
```
**Use Case**: Main application loop should regularly poll for commands to process experiment control, configuration changes, etc.

### Metrics and Status Management

#### `update_metrics(metrics: PingMetrics)`
Update operational metrics sent with heartbeats.
```python
metrics = PingMetrics(
    avg_bpm=72,
    avg_hr=75,
    step="baseline_measurement",
    challengeCount=0,
    longestChallenge="none"
)
plugin.update_metrics(metrics)
```
**Use Case**: Update with current device readings and experiment state.

#### `get_metrics()`
Retrieve current metrics.
```python
current_metrics = plugin.get_metrics()  # Returns PingMetrics
```

#### `set_step(step: str)`
Update the current experiment step.
```python
plugin.set_step("intervention_phase")
```
**Use Case**: Track experiment progression for monitoring and control.

### Status Reporting

#### `report_status(severity, category, code, message, **kwargs)`
Report system status for monitoring.
```python
from status_reporting import StatusSeverity, StatusCategory

status_id = plugin.report_status(
    severity=StatusSeverity.HIGH,
    category=StatusCategory.HARDWARE,
    code="SENSOR_DISCONNECTED",
    message="ECG sensor connection lost",
    component="ecg_monitor"
)
```

#### `resolve_status(status_id: str)`
Mark a status as resolved.
```python
plugin.resolve_status(status_id)
```

#### `get_active_statuses()`
Get all unresolved status reports.
```python
active_issues = plugin.get_active_statuses()  # Returns List[StatusReport]
```

#### `get_status_summary()`
Get status summary statistics.
```python
summary = plugin.get_status_summary()  # Returns Dict[str, Any]
```

### Data Streaming

#### `update_stream_data(stream_data: MinervaStreamData, user_id: str = None)`
Update real-time streaming data.
```python
stream_data = MinervaStreamData(
    mac_address="AA:BB:CC:DD:EE:FF",
    signals=[
        {
            'name': 'ECG',
            'type': 'time_series',
            'data': ecg_readings
        },
        {
            'name': 'BPM',
            'type': 'timestamp',
            'data': bpm_events
        }
    ],
    current_stage="baseline"
)
plugin.update_stream_data(stream_data)
```
**Use Case**: Continuously update with latest sensor readings for real-time monitoring.

#### `get_stream_data(user_id: str = None)`
Retrieve current streaming data.
```python
current_data = plugin.get_stream_data()  # Returns MinervaStreamData
```

### User Session Management

#### `get_active_user_sessions()`
Get list of users currently streaming.
```python
active_users = plugin.get_active_user_sessions()  # Returns List[str]
```

#### `get_user_session_count()`
Get number of active streaming sessions.
```python
session_count = plugin.get_user_session_count()  # Returns int
```

#### `is_user_streaming(user_id: str)`
Check if specific user is streaming.
```python
is_streaming = plugin.is_user_streaming("user123")  # Returns bool
```

#### `get_is_streaming()`
Check if any users are streaming.
```python
has_viewers = plugin.get_is_streaming()  # Returns bool
```

### Monitoring and Diagnostics

#### `get_streaming_metrics()`
Get comprehensive streaming and system metrics.
```python
metrics = plugin.get_streaming_metrics()
# Returns detailed dict with:
# - User activity
# - System health
# - Thread status
# - Queue information
```

#### `get_command_processing_stats()`
Get command processing statistics.
```python
stats = plugin.get_command_processing_stats()
# Returns dict with:
# - Active users count
# - Pending commands
# - Architecture mode
```

## Intended Use Cases

### 1. Medical Device Integration
```python
# Initialize plugin for a medical device
plugin = Plugin(PluginRegistration(device_mac), logger)
plugin.start()

# Main application loop
while device_running:
    # Process any incoming commands
    commands = plugin.pop_commands()
    for cmd in commands:
        handle_device_command(cmd)

    # Update with latest readings
    current_readings = get_device_readings()
    stream_data = create_stream_data(current_readings)
    plugin.update_stream_data(stream_data)

    # Update metrics
    metrics = calculate_metrics(current_readings)
    plugin.update_metrics(metrics)

    time.sleep(0.1)  # 10Hz update rate

plugin.stop()
```

### 2. Simulation Environment
```python
# Simulator that generates mock data
plugin = Plugin(PluginRegistration(sim_mac), logger)
plugin.start()

while simulation_running:
    # Generate simulated sensor data
    mock_signals = generate_mock_signals()
    stream_data = MinervaStreamData(
        mac_address=sim_mac,
        signals=mock_signals,
        current_stage=current_sim_stage
    )
    plugin.update_stream_data(stream_data)

    # Process simulation commands
    commands = plugin.pop_commands()
    for cmd in commands:
        update_simulation_parameters(cmd)
```

### 3. Multi-User Monitoring
```python
# Check who's watching the stream
active_users = plugin.get_active_user_sessions()
if active_users:
    logger.info(f"Streaming to {len(active_users)} users: {active_users}")

    # Adjust data frequency based on viewer count
    if len(active_users) > 10:
        stream_frequency = 5  # Reduce frequency for many users
    else:
        stream_frequency = 10  # Full frequency for few users
```

### 4. Error Handling and Status Reporting
```python
try:
    sensor_data = read_sensor()
except SensorError as e:
    # Report hardware issue
    plugin.report_status(
        severity=StatusSeverity.HIGH,
        category=StatusCategory.HARDWARE,
        code="SENSOR_READ_FAILED",
        message=f"Failed to read sensor: {e}",
        component="sensor_reader"
    )
```

## Architecture Notes

- **Dual Queue System**: Separates critical commands from streaming heartbeats
- **Thread Safety**: All public methods are thread-safe
- **Automatic Cleanup**: User sessions timeout automatically if heartbeats stop
- **Status Reporting**: Comprehensive error tracking and monitoring
- **JSON Serialization**: Handles numpy types automatically via `safe_json_dumps()`

## Dependencies

- RabbitMQ server for message queuing
- Python packages: `pika`, `dataclasses`, `threading`, `json`
- Optional: `numpy` for scientific data types
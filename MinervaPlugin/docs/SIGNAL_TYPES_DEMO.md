# Minerva Signal Types Demo

This document provides examples of all supported signal types in the Minerva system, showing how to create and use each type in Python code.

## Overview

Minerva supports 6 different signal types:
- **Time Series**: Continuous data over time (e.g., ECG, airflow)
- **Timestamp**: Event markers overlaid on time series (e.g., heartbeats, breaths)
- **Single Value**: Current numeric readings (e.g., heart rate, temperature)
- **Status**: Boolean on/off indicators (e.g., device status, alarms)
- **Debug**: Text information for troubleshooting
- **Duration**: Countdown timers with severity levels (e.g., calibration timers, warnings)

## 1. Time Series Signals

Time series signals display continuous data over time as line charts.

```python
from MinervaPlugin.signals import TimeSeriesSignal

# ECG signal example
ecg_signal = TimeSeriesSignal(
    name="ECG",
    type="time_series",
    xUnit="seconds",
    yUnit="mV",
    xWindowMinInSeconds=-10.0,
    xWindowMaxInSeconds=0.0,
    yWindowMinInSeconds=-1.0,
    yWindowMaxInSeconds=1.0,
    data=[
        {"x": -2.0, "y": 0.1},
        {"x": -1.5, "y": 0.8},  # QRS spike
        {"x": -1.0, "y": 0.0},
        {"x": -0.5, "y": 0.2},
        {"x": 0.0, "y": 0.1}
    ]
)

# Airflow signal example
airflow_signal = TimeSeriesSignal(
    name="Airflow",
    type="time_series",
    xUnit="seconds", 
    yUnit="L/min",
    xWindowMinInSeconds=-60.0,
    xWindowMaxInSeconds=0.0,
    yWindowMinInSeconds=-20.0,
    yWindowMaxInSeconds=20.0,
    data=[
        {"x": -5.0, "y": 15.0},   # Inhale
        {"x": -3.0, "y": 0.0},    # Pause
        {"x": -1.0, "y": -12.0},  # Exhale
        {"x": 0.0, "y": 0.0}      # Pause
    ]
)
```

## 2. Timestamp Signals

Timestamp signals mark specific events and are overlaid on time series charts.

```python
from MinervaPlugin.signals import TimestampSignal

# Heartbeat events overlaid on ECG
heartbeat_signal = TimestampSignal(
    name="Heartbeats",
    type="timestamp",
    displayWith="ECG",  # Shows on ECG chart
    data=[
        {"x": -8.0, "y": 1},
        {"x": -7.2, "y": 1},
        {"x": -6.4, "y": 1},
        {"x": -5.6, "y": 1},
        {"x": -4.8, "y": 1}
    ]
)

# Breath events overlaid on airflow
breath_signal = TimestampSignal(
    name="Breaths",
    type="timestamp", 
    displayWith="Airflow",  # Shows on Airflow chart
    data=[
        {"x": -15.0, "y": 1},
        {"x": -11.0, "y": 1},
        {"x": -7.0, "y": 1},
        {"x": -3.0, "y": 1}
    ]
)
```

## 3. Single Value Signals

Single value signals display current numeric readings in compact boxes.

```python
from MinervaPlugin.signals import SingleValueSignal

# Heart rate
heart_rate_signal = SingleValueSignal(
    name="Heart Rate",
    type="single_value",
    valueUnit="bpm",
    data=72.5
)

# Temperature
temperature_signal = SingleValueSignal(
    name="Body Temperature", 
    type="single_value",
    valueUnit="°C",
    data=37.2
)

# Breathing rate
breathing_rate_signal = SingleValueSignal(
    name="Breathing Rate",
    type="single_value", 
    valueUnit="breaths/min",
    data=16.0
)
```

## 4. Status Signals

Status signals show boolean on/off states with colored indicators.

```python
from MinervaPlugin.signals import StatusSignal

# Device connection status
device_status = StatusSignal(
    name="Device Connected",
    type="status",
    data=True  # Shows as green "ON"
)

# Alarm status
alarm_status = StatusSignal(
    name="High Heart Rate Alarm",
    type="status", 
    data=False  # Shows as gray "OFF"
)

# Calibration status
calibration_status = StatusSignal(
    name="Calibration Complete",
    type="status",
    data=True
)
```

## 5. Debug Signals

Debug signals display text information for troubleshooting and system status.

```python
from MinervaPlugin.signals import DebugSignal

# System status
system_debug = DebugSignal(
    name="System Status",
    type="debug",
    data="All systems operational. Last update: 2024-08-18 17:30:45"
)

# Error information
error_debug = DebugSignal(
    name="Recent Errors",
    type="debug",
    data="No errors in the last 24 hours"
)

# Connection info
connection_debug = DebugSignal(
    name="Connection Info",
    type="debug",
    data="Connected to rig MAC: AA:BB:CC:DD:EE:FF, Signal strength: 95%"
)
```

## 6. Duration Signals (NEW)

Duration signals show countdown timers with severity-based color coding. All duration signals are grouped together in a single panel.

```python
from MinervaPlugin.signals import DurationSignal

# Calibration timer (normal priority)
calibration_timer = DurationSignal(
    name="Calibration Timer",
    type="duration",
    duration=120.0,  # 2 minutes remaining
    severity="normal"  # Green color
)

# Warning timer (warning priority)
warning_timer = DurationSignal(
    name="Sample Collection",
    type="duration", 
    duration=30.0,   # 30 seconds remaining
    severity="warning"  # Orange color
)

# Critical timer (danger priority)
critical_timer = DurationSignal(
    name="Emergency Response",
    type="duration",
    duration=10.0,   # 10 seconds remaining  
    severity="danger"  # Red color
)
```

## Complete Example: Creating a Full Signal Payload

```python
def create_demo_signals():
    """Create a complete set of demo signals showing all types."""
    
    signals = [
        # Time series
        TimeSeriesSignal(
            name="ECG", type="time_series", xUnit="s", yUnit="mV",
            xWindowMinInSeconds=-10, xWindowMaxInSeconds=0,
            yWindowMinInSeconds=-1, yWindowMaxInSeconds=1,
            data=[{"x": -i*0.1, "y": math.sin(i*0.5)} for i in range(100)]
        ),
        
        # Timestamp overlay
        TimestampSignal(
            name="R-peaks", type="timestamp", displayWith="ECG",
            data=[{"x": -i*0.8, "y": 1} for i in range(12)]
        ),
        
        # Single values
        SingleValueSignal(name="HR", type="single_value", valueUnit="bpm", data=75),
        SingleValueSignal(name="Temp", type="single_value", valueUnit="°C", data=37.1),
        
        # Status indicators  
        StatusSignal(name="Connected", type="status", data=True),
        StatusSignal(name="Alarm", type="status", data=False),
        
        # Debug info
        DebugSignal(name="System", type="debug", data="Running normally"),
        
        # Duration timers
        DurationSignal(name="Calibration", type="duration", duration=90, severity="normal"),
        DurationSignal(name="Warning", type="duration", duration=15, severity="warning"),
        DurationSignal(name="Critical", type="duration", duration=5, severity="danger")
    ]
    
    return {
        "mac_address": "demo:device:001",
        "stages": [{"name": "Demo", "type": "timed", "duration_in_seconds": 300}],
        "current_stage": "Demo", 
        "signals": [signal.__dict__ for signal in signals]
    }
```

## Severity Levels for Duration Signals

Duration signals support three severity levels that affect their display color:

- **`"normal"`**: Green background - routine timers, normal operations
- **`"warning"`**: Orange background - attention needed, non-critical
- **`"danger"`**: Red background - urgent action required, critical timers

The severity can change dynamically as the timer counts down, allowing for escalating visual alerts.

## Display Behavior

- **Time Series & Timestamps**: Displayed as interactive charts with zoom/pan
- **Single Values**: Compact boxes showing current value with units
- **Status**: ON/OFF chips with green (on) or gray (off) colors  
- **Debug**: Expandable text areas for detailed information
- **Duration**: Grouped countdown timers with MM:SS format and color-coded severity

All signals update in real-time as new data arrives from the streaming system.

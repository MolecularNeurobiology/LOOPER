# MinervaPlugin Directory Structure

This document describes the reorganized directory structure of the MinervaPlugin system.

## Directory Overview

```
MinervaPlugin/
├── main.py                 # Main entry point script
├── __init__.py            # Package initialization
├── requirements.txt       # Python dependencies
├── core/                  # Core plugin functionality
│   ├── __init__.py
│   ├── plugin.py         # Main plugin class
│   ├── rabbitmq_client.py # RabbitMQ communication
│   ├── config.py         # Configuration constants
│   └── status_reporting.py # Status and error reporting
├── models/                # Data models and types
│   ├── __init__.py
│   ├── command.py        # Command utilities (dict-based)
│   ├── signals.py        # Signal data classes
│   └── step.py           # Step/stage definitions
├── simulator/             # Simulation components
│   ├── __init__.py
│   ├── simulator.py      # Main simulator runner
│   ├── simulation.py     # Individual simulation logic
│   ├── rig.py           # Rig state management
│   └── faker.py         # Fake data generation
├── scripts/               # Utility scripts
│   ├── __init__.py
│   ├── run.py           # Run management
│   ├── cleanup_queues.py # Queue cleanup utility
│   └── start.sh         # Shell startup script
├── tests/                 # Test files
│   ├── __init__.py
│   ├── test_dict_commands.py
│   ├── test_streaming_behavior.py
│   ├── test_dual_queue_architecture.py
│   └── test_timeout_functionality.py
├── utils/                 # Utility files and tools
│   ├── __init__.py
│   ├── dual_queue_validation_report.py
│   ├── status_reporting_examples.py
│   └── fake_mac_addresses.txt
├── docs/                  # Documentation
│   ├── README.md
│   ├── INTEGRATION_NOTES.md
│   └── SIGNAL_TYPES_DEMO.md
├── logs/                  # Log files (auto-generated)
└── venv/                  # Python virtual environment
```

## Module Descriptions

### Core (`core/`)
Contains the essential plugin functionality:
- **plugin.py**: Main Plugin class that handles RabbitMQ communication, command processing, and streaming
- **rabbitmq_client.py**: RabbitMQ connection and message handling
- **config.py**: Configuration constants for queues, timeouts, etc.
- **status_reporting.py**: Centralized status and error reporting system

### Models (`models/`)
Data structures and type definitions:
- **command.py**: Command utilities for dict-based commands (getCommandFilename, getStep, legacy mapping)
- **signals.py**: Signal data classes (TimeSeriesSignal, TimestampSignal, etc.)
- **step.py**: Step and stage definitions for experiments

### Simulator (`simulator/`)
Simulation and testing components:
- **simulator.py**: Main simulator that runs multiple rig simulations
- **simulation.py**: Individual simulation logic for a single rig
- **rig.py**: Rig state management and definitions
- **faker.py**: Utilities for generating fake sensor data

### Scripts (`scripts/`)
Utility scripts and runners:
- **run.py**: Run management and execution logic
- **cleanup_queues.py**: RabbitMQ queue cleanup utility
- **start.sh**: Shell script for starting the system

### Tests (`tests/`)
Test suites for different components:
- **test_dict_commands.py**: Tests for the new dict-based command system
- **test_streaming_behavior.py**: Tests for streaming functionality
- **test_dual_queue_architecture.py**: Tests for queue architecture
- **test_timeout_functionality.py**: Tests for timeout handling

### Utils (`utils/`)
Miscellaneous utilities and tools:
- **dual_queue_validation_report.py**: Queue validation and reporting
- **status_reporting_examples.py**: Examples of status reporting usage
- **fake_mac_addresses.txt**: Sample MAC addresses for testing

### Docs (`docs/`)
Documentation files:
- **README.md**: Main documentation
- **INTEGRATION_NOTES.md**: Integration guidelines
- **SIGNAL_TYPES_DEMO.md**: Signal types and usage examples

## Usage

### Running the System

Use the main entry point script:

```bash
# Run the simulator
python main.py simulator

# Run command tests
python main.py test

# Run streaming tests
python main.py streaming-test

# Clean up queues
python main.py cleanup
```

### Importing Modules

The reorganized structure maintains backward compatibility through the main `__init__.py`:

```python
# Import core functionality
from MinervaPlugin import Plugin, PluginRegistration

# Import command utilities
from MinervaPlugin import getCommandFilename, getStep, map_legacy_command

# Import signal types
from MinervaPlugin import TimeSeriesSignal, TimestampSignal, SingleValueSignal

# Import specific modules
from MinervaPlugin.core import plugin, config
from MinervaPlugin.models import command, signals
from MinervaPlugin.simulator import simulator, simulation
```

### Direct Module Access

You can also import directly from subdirectories:

```python
from MinervaPlugin.core.plugin import Plugin
from MinervaPlugin.models.command import getCommandFilename
from MinervaPlugin.simulator.simulation import Simulation
```

## Benefits of This Structure

1. **Clear Separation of Concerns**: Each directory has a specific purpose
2. **Better Maintainability**: Related files are grouped together
3. **Easier Testing**: Tests are isolated in their own directory
4. **Improved Documentation**: Docs are centralized and organized
5. **Scalability**: Easy to add new modules in appropriate directories
6. **Backward Compatibility**: Existing imports continue to work

## Migration Notes

- All existing imports should continue to work through the main `__init__.py`
- The main entry point (`main.py`) provides a unified interface
- Tests can be run individually or through the main script
- Documentation is now centralized in the `docs/` directory

This structure follows Python packaging best practices and makes the codebase more professional and maintainable.

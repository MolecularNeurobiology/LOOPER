# Import data models (these don't have complex dependencies)
from .models import command
from .models import signals
from .models import step

# Expose commonly used functions from models
from .models.command import getCommandFilename, getStep, map_legacy_command, LEGACY_COMMAND_MAPPING, SEEDED_COMMANDS
from .models.signals import (
    TimeSeriesSignal, TimestampSignal, SingleValueSignal,
    StatusSignal, DebugSignal, DurationSignal, Signal
)

# Lazy import for plugin module to avoid dependency issues
class _PluginModule:
    """Lazy loader for plugin module to handle dependencies gracefully."""
    def __getattr__(self, name):
        try:
            from .core import plugin as _plugin_module
            return getattr(_plugin_module, name)
        except ImportError as e:
            raise ImportError(f"Could not import plugin module. Missing dependencies: {e}")

plugin = _PluginModule()

# Core classes are imported on-demand to avoid dependency issues
# Use: from MinervaPlugin.core.plugin import Plugin, PluginRegistration
# Use: from MinervaPlugin.simulator.simulator import main as run_simulator

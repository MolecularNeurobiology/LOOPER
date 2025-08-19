"""
PCC Command Dispatcher Example (not integrated)

This is a minimal, pluggable example of a string-based command dispatcher
for the PCC side. Do NOT import into runtime yet.

Integration points are marked clearly. The plugin now passes raw command
dicts (except stream heartbeats). PCC should consume these and call handlers.
"""
from typing import Any, Callable, Dict, Optional

# Type alias for a command envelope (from Minerva API via plugin)
CommandEnvelope = Dict[str, Any]

class PCCDispatcher:
    """String-based command dispatcher for PCC.

    Usage:
      dispatcher = PCCDispatcher()
      dispatcher.register_handler('start', lambda cmd: pcc.start_run(cmd.get('payload')))
      dispatcher.dispatch({'type': 'start', 'payload': {'assayId': 'A-123'}})
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[CommandEnvelope], None]] = {}

    def register_handler(self, name: str, handler: Callable[[CommandEnvelope], None]) -> None:
        """Register a handler for a command name (lowercased)."""
        self._handlers[name.lower()] = handler

    def unregister_handler(self, name: str) -> None:
        self._handlers.pop(name.lower(), None)

    def dispatch(self, command: CommandEnvelope) -> bool:
        """Dispatch a command to a registered handler.

        Returns True if handled, False otherwise.
        """
        if not isinstance(command, dict):
            return False
        name = str(command.get('type', '')).lower()
        if not name:
            return False
        handler = self._handlers.get(name)
        if handler:
            handler(command)
            return True
        return False

# --- Integration points ---
# 1) Where commands are polled from the plugin (e.g., in simulator loop or PCC main):
#
#    commands = plugin.pop_commands()
#    for cmd in commands:
#        if not dispatcher.dispatch(cmd):
#            logger.debug(f"Unhandled command: {cmd.get('type')}")
#
# 2) Register concrete PCC behaviors:
#
#    dispatcher.register_handler('start', lambda cmd: pcc.start_run(cmd.get('payload')))
#    dispatcher.register_handler('go_to_next', lambda cmd: pcc.go_to_next_step())
#    dispatcher.register_handler('go_to_step', lambda cmd: pcc.go_to_step((cmd.get('payload') or {}).get('index')))
#
# 3) Steps ownership: PCC resolves steps from assay settings/state internally.
#    The 'start' command should not expect inline 'steps' in payload.
#
# 4) Extensibility: new commands only need a handler registration in PCC code.


from typing import Any, Dict, Optional

# Legacy command mapping for backward compatibility
LEGACY_COMMAND_MAPPING = {
    'start': 'initialize_rig',
    'load_pups': 'send_filename'
}

# Current seeded command types (for reference)
SEEDED_COMMANDS = [
    'initialize_rig',    # Replaces 'start'
    'go_to_next',       # Unchanged
    'go_to_step',       # Unchanged (payload structure updated)
    'stream',           # Unchanged
    'stop_stream',      # Unchanged
    'stop_experiment',  # New command
    'send_filename'     # Replaces 'load_pups'
]



# Utility functions for extracting payload data from commands that have payloads

def getCommandFilename(command_data: Dict[str, Any]) -> Optional[str]:
    """Extract filename from send_filename command payload"""
    if not isinstance(command_data, dict):
        return None

    payload = command_data.get('payload', {})
    if not isinstance(payload, dict):
        return None

    return payload.get('filename')

def getStep(command_data: Dict[str, Any]) -> Optional[int]:
    """Extract step number from go_to_step command payload"""
    if not isinstance(command_data, dict):
        return None

    payload = command_data.get('payload', {})
    if not isinstance(payload, dict):
        return None

    step = payload.get('step')
    if step is not None:
        try:
            return int(step)
        except (ValueError, TypeError):
            return None

    return None

# Legacy command mapping for backward compatibility
def map_legacy_command(command_type: str) -> str:
    """Map legacy command type to new seeded command type"""
    return LEGACY_COMMAND_MAPPING.get(command_type, command_type)

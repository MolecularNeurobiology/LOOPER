from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
try:
    from step import Step
except:
    print("attempting relative import of step")
    from .step import Step

class COMMANDS(Enum):
    CONFIRM_REGISTER = 0
    START = 1
    GO_TO_NEXT_STEP = 2
    GO_TO_PREV_STEP = 3
    GO_TO_STEP = 4
    STREAM = 5  # New command type for streaming
    STOP_STREAM = 6  # New command type for stopping the stream

class Command(ABC):
    def __init__(self, command_type: COMMANDS, payload: Dict[str, Any]):
        self.type = command_type
        self.payload = payload
    
    def get_payload(self):
        return self.payload

@dataclass
class StartPayload:
    steps: list[Step]

@dataclass
class GoToPayload:
    step: Step

class StartCommand(Command):
    def __init__(self, payload: StartPayload):
        super().__init__(command_type=COMMANDS.START, payload=payload)

class GoToNextStep(Command):
    def __init__(self):
        super().__init__(command_type=COMMANDS.GO_TO_NEXT_STEP, payload=None)

class GoToStep(Command):
    def __init__(self, payload: GoToPayload):
        super().__init__(command_type=COMMANDS.GO_TO_STEP, payload=payload)

# New classes for stream data based on TypeScript types
class StageType(Enum):
    WAIT_FOR_USER = "wait_for_user"
    TIMED = "timed"
    WAIT_FOR_CONDITION = "wait_for_condition"

class SignalType(Enum):
    TIME_SERIES = "time_series"
    TIMESTAMP = "timestamp"
    SINGLE_VALUE = "single_value"
    STATUS = "status"
    DEBUG = "debug"

@dataclass
class TimeSeriesDataPoint:
    x: float
    y: float

@dataclass
class Stage:
    """Stage in the Minerva workflow."""
    name: str
    type: str  # StageType as string
    durationInSeconds: Optional[int] = None

@dataclass
class BaseSignal:
    """Base class for signals."""
    name: str
    type: str  # SignalType as string
    displayWith: Optional[str] = field(default=None)  # Optional field with explicit default

@dataclass
class TimeSeriesSignal(BaseSignal):
    """Time series signal with x,y data points."""
    xUnit: str = ""
    yUnit: str = ""
    xWindowMinInSeconds: float = 0.0
    xWindowMaxInSeconds: float = 300.0
    yWindowMinInSeconds: float = 0.0
    yWindowMaxInSeconds: float = 200.0
    data: List[Dict[str, float]] = field(default_factory=list)

@dataclass
class TimestampSignal(BaseSignal):
    """Timestamp signal showing events."""
    data: List[Dict[str, float]] = field(default_factory=list)

@dataclass
class SingleValueSignal(BaseSignal):
    """Signal with a single numeric value."""
    valueUnit: str = ""
    data: float = 0.0

@dataclass
class StatusSignal(BaseSignal):
    """Signal with a boolean status."""
    data: bool = False

@dataclass
class DebugSignal(BaseSignal):
    """Signal with debug text."""
    data: str = ""

# Union type for Signal
Signal = Union[TimeSeriesSignal, TimestampSignal, SingleValueSignal, StatusSignal, DebugSignal]

# Stream Command
class StreamCommand(Command):
    """Command to initiate or update streaming of Minerva data."""
    def __init__(self, command_data: Dict[str, Any]):
        # Extract payload from the command data
        payload = command_data.get('payload', {})
        super().__init__(command_type=COMMANDS.STREAM, payload=payload)
        # Store the full command data to access top-level fields
        self._command_data = command_data

    def get_user_id(self) -> str:
        """Get the user ID from the command (checks both top level and payload)."""
        # First check top level (where frontend sends it)
        user_id = self._command_data.get('userId')
        if user_id is not None:
            return str(user_id)

        # Fallback to payload (for backward compatibility)
        user_id = self.payload.get('userId')
        if user_id is not None:
            return str(user_id)

        # Final fallback
        return 'default_user'

    def get_mac_address(self) -> str:
        """Get the MAC address from the command (checks both top level and payload)."""
        # First check top level (where frontend sends it)
        mac_address = self._command_data.get('macAddress')
        if mac_address is not None:
            return mac_address

        # Fallback to payload (for backward compatibility)
        return self.payload.get('macAddress')

    def get_stages(self) -> List[Dict[str, Any]]:
        """Get the stages from the payload or an empty list if none."""
        return self.payload.get('stages', [])

    def get_signals(self) -> List[Dict[str, Any]]:
        """Get the signals from the payload or an empty list if none."""
        return self.payload.get('signals', [])

    def get_current_stage(self) -> Optional[str]:
        """Get the current stage from the payload or None if not specified."""
        return self.payload.get('currentStage')

# Stop Stream Command
class StopStreamCommand(Command):
    """Command to stop streaming data."""
    def __init__(self):
        super().__init__(command_type=COMMANDS.STOP_STREAM, payload=None)

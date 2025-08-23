from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

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
    DURATION = "duration"

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

@dataclass
class DurationSignal(BaseSignal):
    """Signal with duration countdown and severity status."""
    duration: float = 0.0  # Duration in seconds
    severity: str = "normal"  # "normal", "warning", "danger"

# Union type for Signal
Signal = Union[TimeSeriesSignal, TimestampSignal, SingleValueSignal, StatusSignal, DebugSignal, DurationSignal]

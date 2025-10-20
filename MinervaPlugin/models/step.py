from dataclasses import dataclass
from typing import Optional

@dataclass
class Step:
    name: str
    type: Optional[str] = None  # 'wait_for_user', 'timed', 'wait_for_condition'
    durationInSeconds: Optional[int] = None  # Duration for timed steps
    duration_in_seconds: Optional[int] = None  # Alternative snake_case naming
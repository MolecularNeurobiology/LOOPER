from abc import ABC, abstractmethod
from dataclasses import dataclass

from enum import Enum
from typing import Any, Dict

from step import Step

class COMMANDS(Enum):
    CONFIRM_REGISTER = 0
    START = 1
    GO_TO_NEXT_STEP = 2
    GO_TO_PREV_STEP = 3
    GO_TO_STEP = 4

class Command(ABC):
    def __init__(self, command_type: COMMANDS, payload: Dict[str, Any]):
        self.type = command_type
        self.payload = payload

    def get_payload(self):
        return self.payload

@dataclass
class StartPayload:
    steps: list[Step]

class StartCommand(Command):
    def __init__(self, payload: StartPayload):
        super().__init__(command_type=COMMANDS.START, payload=payload)

class GoToNextStep(Command):
    def __init__(self):
        super().__init__(command_type=COMMANDS.GO_TO_NEXT_STEP, payload=None)
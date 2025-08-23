from enum import Enum


class RIG_STATE(Enum):
    WAITING_TO_REGISTER = "WAITING_TO_REGISTER"
    IDLE = "IDLE"
    RUNNING = "RUNNING"

class Rig:
    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.state = RIG_STATE.WAITING_TO_REGISTER
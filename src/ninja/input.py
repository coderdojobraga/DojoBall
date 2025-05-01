from dataclasses import dataclass

@dataclass
class Input:
    up: bool
    down: bool
    left: bool
    right: bool
    kick: bool

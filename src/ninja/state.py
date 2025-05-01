from dataclasses import dataclass
from enum import Enum, auto


SCREEN_WIDTH = 720
SCREEN_HEIGHT = 720


class Team(Enum):
    RED = auto()
    BLUE = auto()


@dataclass
class Player:
    name: str
    team: Team
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    mass: float
    drag_coefficient: float
    kick: bool


@dataclass
class Ball:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    mass: float
    drag_coefficient: float


@dataclass
class Post:
    team: Team
    x: float
    y: float
    radius: float


@dataclass
class State:
    field_width: int
    field_height: int
    players: dict[tuple[str, int], Player]
    ball: Ball
    posts: list[Post]

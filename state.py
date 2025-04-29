from enum import Enum, auto


SCREEN_WIDTH = 720
SCREEN_HEIGHT = 720


class Team(Enum):
    RED = auto()
    BLUE = auto()

    def __str__(self) -> str:
        return self.name.lower()


class State:
    def __init__(self) -> None:
        self.field_width: int = SCREEN_WIDTH
        self.field_height: int = SCREEN_HEIGHT
        self.players: dict[tuple[str, int], Player] = {}
        self.ball: Ball = Ball()
        self.posts: list[Post] = [
            Post(Team.RED, 20, SCREEN_HEIGHT / 2 + 80),
            Post(Team.RED, 20, SCREEN_HEIGHT / 2 - 80),
            Post(Team.BLUE, SCREEN_WIDTH - 20, SCREEN_HEIGHT / 2 + 80),
            Post(Team.BLUE, SCREEN_WIDTH - 20, SCREEN_HEIGHT / 2 - 80),
        ]

    def __repr__(self) -> str:
        return f"State({self.players}, {self.ball})"


class Circle:
    def __init__(self, x: float = 0, y: float = 0, vx: float = 0, vy: float = 0, radius: float = 0) -> None:
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.radius: float = radius
        self.mass: float = 1
        self.drag_coefficient: float = 0.8


class Player(Circle):
    def __init__(self, name: str, team: Team, x: float = 0, y: float = 0, vx: float = 0, vy: float = 0, radius: float = 45) -> None:
        self.name = name
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.radius: float = radius
        self.mass: float = 1
        self.drag_coefficient: float = 0.96
        self.kick: bool = False
        self.team: Team = team
        # self.kick_power: float = 0.5

    def __repr__(self) -> str:
        return f"Player({self.x}, {self.y})"


class Ball(Circle):
    def __init__(self, x: float = 0, y: float = 0, vx: float = 0, vy: float = 0, radius: float = 30) -> None:
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.radius: float = radius
        self.mass: float = 0.5
        self.drag_coefficient: float = 0.99

    def __repr__(self) -> str:
        return f"Ball({self.x}, {self.y})"


class Post(Circle):
    def __init__(self, team: Team, x: float = 0, y: float = 0, radius: float = 15) -> None:
        self.team: Team = team
        self.x: float = x
        self.y: float = y
        self.radius: float = radius

    def __repr__(self) -> str:
        return f"Post({self.x}, {self.y})"

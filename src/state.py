from enum import Enum, auto


SCREEN_WIDTH = 1080
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
        self.posts: dict[str, Post] = {
            "tl": Post(Team.RED, 50, SCREEN_HEIGHT / 2 + 80),
            "bl": Post(Team.RED, 50, SCREEN_HEIGHT / 2 - 80),
            "tr": Post(Team.BLUE, SCREEN_WIDTH - 50, SCREEN_HEIGHT / 2 + 80),
            "br": Post(Team.BLUE, SCREEN_WIDTH - 50, SCREEN_HEIGHT / 2 - 80),
        }
        self.score_red: int = 0
        self.score_blue: int = 0
        self.timer = 0


class Circle:
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        vx: float = 0,
        vy: float = 0,
        radius: float = 0,
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.radius: float = radius
        self.mass: float = 1
        self.drag_coefficient: float = 0.8


class Player(Circle):
    def __init__(
        self,
        name: str,
        team: Team,
        x: float = 0,
        y: float = 0,
        vx: float = 0,
        vy: float = 0,
        radius: float = 45,
    ) -> None:
        super().__init__(x, y, vx, vy, radius)
        self.name: str = name
        self.team: Team = team
        self.drag_coefficient: float = 0.96
        self.kick: bool = False
        # self.kick_power: float = 0.5


class Ball(Circle):
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        vx: float = 0,
        vy: float = 0,
        radius: float = 30,
    ) -> None:
        super().__init__(x, y, vx, vy, radius)
        self.mass: float = 0.5
        self.drag_coefficient: float = 0.99


class Post(Circle):
    def __init__(
        self, team: Team, x: float = 0, y: float = 0, radius: float = 15
    ) -> None:
        super().__init__(x, y, radius=radius)
        self.team: Team = team

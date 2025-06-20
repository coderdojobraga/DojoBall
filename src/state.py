from enum import Enum, auto


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

FIELD_SCALE = 70
FIELD_WIDTH = 21 * FIELD_SCALE
FIELD_HEIGHT = 10 * FIELD_SCALE

FIELD_TL_X = round((SCREEN_WIDTH - FIELD_WIDTH) / 2)
FIELD_TL_Y = round((SCREEN_HEIGHT - FIELD_HEIGHT) / 2)
FIELD_BR_X = FIELD_TL_X + FIELD_WIDTH
FIELD_BR_Y = FIELD_TL_Y + FIELD_HEIGHT

PLAYER_AREA_WIDTH = FIELD_WIDTH + 2 * 145 # 145 is the diameter of a player + 55
PLAYER_AREA_HEIGHT = FIELD_HEIGHT + 2 * 90 # 90 is the diameter of a player

PLAYER_AREA_TL_X = round((SCREEN_WIDTH - PLAYER_AREA_WIDTH) / 2)
PLAYER_AREA_TL_Y = round((SCREEN_HEIGHT - PLAYER_AREA_HEIGHT) / 2)
PLAYER_AREA_BR_X = PLAYER_AREA_TL_X + PLAYER_AREA_WIDTH
PLAYER_AREA_BR_Y = PLAYER_AREA_TL_Y + PLAYER_AREA_HEIGHT


class Team(Enum):
    RED = auto()
    BLUE = auto()

    def __str__(self) -> str:
        return self.name.lower()


class State:
    def __init__(self) -> None:
        self.player_area_coords: tuple[int, int, int, int] = (PLAYER_AREA_TL_X, PLAYER_AREA_TL_Y, PLAYER_AREA_BR_X, PLAYER_AREA_BR_Y)
        self.field_coords: tuple[int, int, int, int] = (FIELD_TL_X, FIELD_TL_Y, FIELD_BR_X, FIELD_BR_Y)
        self.players: dict[tuple[str, int], Player] = {}
        self.ball: Ball = Ball()
        self.posts: dict[str, Post] = {
            "tl": Post(Team.RED, FIELD_TL_X, SCREEN_HEIGHT / 2 - 150),
            "bl": Post(Team.RED, FIELD_TL_X, SCREEN_HEIGHT / 2 + 150),
            "tr": Post(Team.BLUE, FIELD_BR_X, SCREEN_HEIGHT / 2 - 150),
            "br": Post(Team.BLUE, FIELD_BR_X, SCREEN_HEIGHT / 2 + 150),
        }
        self.score_red: int = 0
        self.score_blue: int = 0
        self.clock: int = 0 # in seconds


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
        self.kick_locked: bool = False
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

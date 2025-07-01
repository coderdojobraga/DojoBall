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
        self.match_manager = MatchManager()


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

class MatchState(Enum):
    PLAYING = auto()
    OVERTIME = auto()
    BREAK = auto()
    PAUSED = auto()

class MatchManager:
    def __init__(self):
        self.state = MatchState.BREAK
        self.match_duration = 120  # 2 minutos
        self.break_duration = 30   # 30 segundos
        self.overtime_duration = 60 # 1 minuto
        self.time_remaining = self.break_duration
        self.state_before_pause = None

    def update(self, dt, score_red, score_blue):
        if self.state != MatchState.PAUSED:
            self.time_remaining -= dt
            if self.time_remaining <= 0:
                self.time_remaining = 0
                self._change_state(score_red, score_blue)
                print(f"State changed to {self.state}")

    def _change_state(self, score_red, score_blue):
        if self.state == MatchState.PLAYING:
            if score_red == score_blue:
                self.state = MatchState.OVERTIME
                self.time_remaining = self.overtime_duration
                print("Match ended in a tie, starting overtime.")
            else:
                self.state = MatchState.BREAK
                self.time_remaining = self.break_duration
                print("Match ended, break started")
        elif self.state == MatchState.OVERTIME:
            self.state = MatchState.BREAK
            self.time_remaining = self.break_duration
            print("Overtime ended, break started")
        elif self.state == MatchState.BREAK:
            self.state = MatchState.PLAYING
            self.time_remaining = self.match_duration
            print("Break ended, match started")

    def start_match(self):
        if self.state == MatchState.BREAK:
            self.state = MatchState.PLAYING
            self.time_remaining = self.match_duration

    def pause_match(self):
        if self.state in [MatchState.PLAYING, MatchState.OVERTIME]:
            self.state_before_pause = self.state
            self.state = MatchState.PAUSED

    def resume_match(self):
        if self.state == MatchState.PAUSED and self.state_before_pause:
            self.state = self.state_before_pause
            self.state_before_pause = None

    def set_match_time(self, seconds):
        self.match_duration = seconds

    def set_break_time(self, seconds):
        self.break_duration = seconds

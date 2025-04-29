import math
import pickle
from itertools import combinations, product
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

    def moving_circles(self):
        yield from self.players.values()
        yield self.ball

    def handle_collisions(self):
        # Could handle collisions between players first and then between players and ball and check if player is kicking
        for c1, c2 in combinations(self.moving_circles(), 2):
            dx = c2.x - c1.x
            dy = c2.y - c1.y
            distance_sqr = dx ** 2 + dy ** 2
            radius_sum = c1.radius + c2.radius

            # Check for overlap
            if distance_sqr < radius_sum ** 2:
                # Resolve overlap
                distance = math.sqrt(distance_sqr)
                nx = dx / distance
                ny = dy / distance
                overlap = 0.5 * (radius_sum - distance)
                c1.x -= overlap * nx
                c1.y -= overlap * ny
                c2.x += overlap * nx
                c2.y += overlap * ny

                # Resolve velocity
                kx = c1.vx - c2.vx
                ky = c1.vy - c2.vy
                p = 2 * (nx * kx + ny * ky) / (c1.mass + c2.mass)
                c1.vx -= p * c2.mass * nx
                c1.vy -= p * c2.mass * ny
                c2.vx += p * c1.mass * nx
                c2.vy += p * c1.mass * ny

        # Check for collisions with walls
        for c in self.moving_circles():
            if c.x < c.radius:
                c.x = c.radius
                c.vx *= -1
            if c.x >= SCREEN_WIDTH - c.radius:
                c.x = SCREEN_WIDTH - 1 - c.radius
                c.vx *= -1
            if c.y < c.radius:
                c.y = c.radius
                c.vy *= -1
            if c.y >= SCREEN_HEIGHT - c.radius:
                c.y = SCREEN_HEIGHT - 1 - c.radius
                c.vy *= -1

        # Check for collisions with posts
        for c, p in product(self.moving_circles(), self.posts):
            dx = p.x - c.x
            dy = p.y - c.y
            distance_sqr = dx ** 2 + dy ** 2
            radius_sum = c.radius + p.radius

            # Check for overlap
            if distance_sqr < radius_sum ** 2:
                # Resolve overlap
                distance = math.sqrt(distance_sqr)
                nx = dx / distance
                ny = dy / distance
                overlap = radius_sum - distance
                c.x -= overlap * nx
                c.y -= overlap * ny

                # Resolve velocity
                dp = 2 * (nx * c.vx + ny * c.vy)
                c.vx -= dp * nx
                c.vy -= dp * ny

    def handle_kicks(self):
        for player in self.players.values():
            if player.kick: 
                dx = self.ball.x - player.x
                dy = self.ball.y - player.y
                dist = dx ** 2 + dy ** 2

                # Verifica se a bola está dentro do raio de pontapé
                if dist < (player.radius + self.ball.radius + 20) ** 2:
                    distance = math.sqrt(dist)
                    self.ball.vx += 0.5 * dx / distance
                    self.ball.vy += 0.5 * dy / distance

    def clear_kicks(self):
        for player in self.players.values():
            player.kick = False

    def step(self, clock, inputs, state_lock, send_cond, last_state_pickle):
        with state_lock:
            for address, player in self.players.items():
                if address in inputs:
                    player.apply_input(inputs[address])
                    del inputs[address]

            for player in self.players.values():
                player.update_position()

            self.ball.update_position()

            self.handle_collisions()

            self.handle_kicks()

            data = pickle.dumps(self)
            last_state_pickle[:] = len(data).to_bytes(4, "big") + data

            with send_cond:
                send_cond.notify_all()

            self.clear_kicks()

        clock.tick(60)

        return True


class Circle:
    def __init__(self, x: float = 0, y: float = 0, vx: float = 0, vy: float = 0, radius: float = 0) -> None:
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.radius: float = radius
        self.mass: float = 1
        self.drag_coefficient: float = 0.8

    def update_position(self):
        # Update position
        self.x += self.vx * 5.5
        self.y += self.vy * 5.5

        # Apply drag 
        self.vx *= self.drag_coefficient
        self.vy *= self.drag_coefficient

        # Clamp velocity near zero
        if self.vx ** 2 + self.vy ** 2 < 0.001:
            self.vx = 0
            self.vy = 0


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

    def apply_input(self, input) -> None:
        x = (-1 if input.left else 0) + (1 if input.right else 0)
        y = (-1 if input.up else 0) + (1 if input.down else 0)

        if x or y:
            move_magnitude = math.sqrt(x ** 2 + y ** 2)
            mx = x / move_magnitude
            my = y / move_magnitude

            if input.kick:
                self.vx += 0.05 * 0.7 * mx
                self.vy += 0.05 * 0.7 * my
            else:
                self.vx += 0.05 * mx
                self.vy += 0.05 * my

            # Normalize velocity to ensure norm is 1
            magnitude = math.sqrt(self.vx ** 2 + self.vy ** 2)
            if magnitude > 1:
                self.vx /= magnitude
                self.vy /= magnitude

        if input.kick:
            self.kick = True


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

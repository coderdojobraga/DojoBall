from typing import Dict, Iterator, Tuple
import math
from itertools import combinations
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
        self.players: Dict[Tuple[str, int], Player] = {}
        self.ball: Ball = Ball()

    def __repr__(self) -> str:
        return f"State({self.players}, {self.ball})"

    def all_circles(self):
        yield from self.players.values()
        yield self.ball

    def handle_collisions(self):
        # Could handle collisions between players first and then between players and ball and check if player is kicking
        for c1, c2 in combinations(self.all_circles(), 2):
            dx = c2.x - c1.x
            dy = c2.y - c1.y
            dist = dx**2 + dy**2
            radius_sum = c1.radius + c2.radius

            # Check for overlap
            if dist < radius_sum**2:
                # Resolve overlap
                distance = math.sqrt(dist)

                # Normal vector
                nx = dx / distance
                ny = dy / distance

                overlap = 0.5 * (distance - radius_sum)
                c1.x += overlap * nx
                c1.y += overlap * ny
                c2.x -= overlap * nx
                c2.y -= overlap * ny

                # Resolve velocity
                kx = c1.vx - c2.vx
                ky = c1.vy - c2.vy
                p = 2 * (nx * kx + ny * ky) / (c1.mass + c2.mass)
                c1.vx -= p * c2.mass * nx
                c1.vy -= p * c2.mass * ny
                c2.vx += p * c1.mass * nx
                c2.vy += p * c1.mass * ny

    def handle_kicks(self):
        for player in self.players.values():
            if player.kick: 
                dx = self.ball.x - player.x
                dy = self.ball.y - player.y
                dist = dx**2 + dy**2

                # Check for overlap
                if dist < (player.radius + self.ball.radius + 20)**2:
                    # Resolve overlap
                    distance = math.sqrt(dist)

                    # Normal vector
                    nx = dx / distance
                    ny = dy / distance

                    self.ball.vx += 0.5 * nx
                    self.ball.vy += 0.5 * ny 


    def clear_kicks(self):
        for player in self.players.values():
            player.kick = False


class Circle:
    def __init__(self, x: float = 0, y: float = 0, vx: float = 0, vy: float = 0, radius: float = 0) -> None:
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.radius: float = radius
        self.mass: float = 1
        self.drag_coefficient: float = 0.8

    def update_position(self, dt):
        # print(dt, dt * 60)

        # Update position
        self.x += self.vx * 5.5 # dt * 350
        self.y += self.vy * 5.5 # dt * 350

        # Apply drag 
        self.vx *= self.drag_coefficient # * dt * 60
        self.vy *= self.drag_coefficient # * dt * 60

        # Wrap around screen
        if self.x < 0:
            self.x += SCREEN_WIDTH
        if self.x >= SCREEN_WIDTH:
            self.x -= SCREEN_WIDTH
        if self.y < 0:
            self.y += SCREEN_HEIGHT
        if self.y >= SCREEN_HEIGHT:
            self.y -= SCREEN_HEIGHT

        # Clamp velocity near zero
        if self.vx**2 + self.vy**2 < 0.001:
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

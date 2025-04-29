import math
import pickle
from itertools import combinations, product


SCREEN_WIDTH = 720
SCREEN_HEIGHT = 720


def moving_circles(state):
    yield from state.players.values()
    yield state.ball

def handle_collisions(state):
    # Could handle collisions between players first and then between players and ball and check if player is kicking
    for c1, c2 in combinations(state.moving_circles(), 2):
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
    for c in moving_circles(state):
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
    for c, p in product(state.moving_circles(), state.posts):
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

def handle_kicks(state):
    for player in state.players.values():
        if player.kick: 
            dx = state.ball.x - player.x
            dy = state.ball.y - player.y
            dist = dx ** 2 + dy ** 2

            # Verifica se a bola está dentro do raio de pontapé
            if dist < (player.radius + state.ball.radius + 20) ** 2:
                distance = math.sqrt(dist)
                state.ball.vx += 0.5 * dx / distance
                state.ball.vy += 0.5 * dy / distance

def clear_kicks(state):
    for player in state.players.values():
        player.kick = False

def step(state, clock, inputs, state_lock, send_cond, last_state_pickle):
    with state_lock:
        for address, player in state.players.items():
            if address in inputs:
                apply_input(player, inputs[address])
                del inputs[address]

        for player in state.players.values():
            update_position(player)

        update_position(state.ball)

        handle_collisions(state)

        handle_kicks(state)

        data = pickle.dumps(state)
        last_state_pickle[:] = len(data).to_bytes(4, "big") + data

        with send_cond:
            send_cond.notify_all()

        clear_kicks(state)

    clock.tick(60)


    return True


def update_position(circle):
    # Update position
    circle.x += circle.vx * 5.5
    circle.y += circle.vy * 5.5

    # Apply drag 
    circle.vx *= circle.drag_coefficient
    circle.vy *= circle.drag_coefficient

    # Clamp velocity near zero
    if circle.vx ** 2 + circle.vy ** 2 < 0.001:
        circle.vx = 0
        circle.vy = 0


def apply_input(player, input) -> None:
    x = (-1 if input.left else 0) + (1 if input.right else 0)
    y = (-1 if input.up else 0) + (1 if input.down else 0)

    if x or y:
        move_magnitude = math.sqrt(x ** 2 + y ** 2)
        mx = x / move_magnitude
        my = y / move_magnitude

        if input.kick:
            player.vx += 0.05 * 0.7 * mx
            player.vy += 0.05 * 0.7 * my
        else:
            player.vx += 0.05 * mx
            player.vy += 0.05 * my

        # Normalize velocity to ensure norm is 1
        magnitude = math.sqrt(player.vx ** 2 + player.vy ** 2)
        if magnitude > 1:
            player.vx /= magnitude
            player.vy /= magnitude

    if input.kick:
        player.kick = True

import math
import pickle
from itertools import combinations, product
from state import SCREEN_HEIGHT, SCREEN_WIDTH


def moving_circles(state):
    yield from state.players.values()
    yield state.ball


def step(state, clock, inputs, state_lock, send_cond, last_state_pickle):
    # Track previous input for edge-triggered kick
    if not hasattr(step, "prev_inputs"):
        step.prev_inputs = {}
    prev_inputs = step.prev_inputs
    with state_lock:
        for address, player in state.players.items():
            if address in inputs:
                prev_input = prev_inputs.get(address)
                curr_input = inputs[address]
                apply_input(player, curr_input, prev_input)
                prev_inputs[address] = curr_input
                del inputs[address]

        for circle in moving_circles(state):
            update_position(circle)

        handle_collisions(state)

        handle_kicks(state)

        check_goal(state)

        data = pickle.dumps(state)
        last_state_pickle[:] = len(data).to_bytes(4, "big") + data

        with send_cond:
            send_cond.notify_all()

        clear_kicks(state)

    clock.tick(60)

    return True


def handle_collisions(state):
    # Could handle collisions between players first and then between players and ball and check if player is kicking
    for c1, c2 in combinations(moving_circles(state), 2):
        dx = c2.x - c1.x
        dy = c2.y - c1.y
        distance_sqr = dx**2 + dy**2
        radius_sum = c1.radius + c2.radius

        # Check for overlap
        if distance_sqr < radius_sum**2:
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
    for c, p in product(moving_circles(state), state.posts.values()):
        dx = p.x - c.x
        dy = p.y - c.y
        distance_sqr = dx**2 + dy**2
        radius_sum = c.radius + p.radius

        # Check for overlap
        if distance_sqr < radius_sum**2:
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
        if player.kick and not player.kick_locked:
            dx = state.ball.x - player.x
            dy = state.ball.y - player.y
            dist = dx**2 + dy**2

            if dist < (player.radius + state.ball.radius + 20) ** 2:
                distance = math.sqrt(dist)
                state.ball.vx += 0.5 * dx / distance
                state.ball.vy += 0.5 * dy / distance
                player.kick_locked = True


def clear_kicks(state):
    for player in state.players.values():
        player.kick = False


def update_position(circle):
    # Update position
    circle.x += circle.vx * 5.5
    circle.y += circle.vy * 5.5

    # Apply drag
    circle.vx *= circle.drag_coefficient
    circle.vy *= circle.drag_coefficient

    # Clamp velocity near zero
    if circle.vx**2 + circle.vy**2 < 0.001:
        circle.vx = 0
        circle.vy = 0


def apply_input(player, input) -> None:
    x = (-1 if input.left else 0) + (1 if input.right else 0)
    y = (-1 if input.up else 0) + (1 if input.down else 0)

    if x or y:
        move_magnitude = math.sqrt(x**2 + y**2)
        mx = x / move_magnitude
        my = y / move_magnitude

        if input.kick:
            player.vx += 0.05 * 0.7 * mx
            player.vy += 0.05 * 0.7 * my
        else:
            player.vx += 0.05 * mx
            player.vy += 0.05 * my

        # Normalize velocity to ensure norm is 1
        magnitude = math.sqrt(player.vx**2 + player.vy**2)
        if magnitude > 1:
            player.vx /= magnitude
            player.vy /= magnitude

    if not input.kick:
        player.kick_locked = False
    player.kick = input.kick and not player.kick_locked


def check_goal(state):
    if (
        state.ball.x < state.posts["tl"].x
        and state.posts["bl"].y < state.ball.y < state.posts["tl"].y
    ):
        # Red team scores
        state.score_red += 1
        reset_ball(state)
    elif (
        state.ball.x > state.posts["tr"].x
        and state.posts["br"].y < state.ball.y < state.posts["tr"].y
    ):
        # Blue team scores
        state.score_blue += 1
        reset_ball(state)


def reset_ball(state):
    state.ball.x = SCREEN_WIDTH / 2
    state.ball.y = SCREEN_HEIGHT / 2
    state.ball.vx = 0
    state.ball.vy = 0

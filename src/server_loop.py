import math
import pickle
import pygame
from itertools import combinations, product
from state import FIELD_WIDTH, PLAYER_AREA_BR_X, PLAYER_AREA_HEIGHT, PLAYER_AREA_TL_X, PLAYER_AREA_TL_Y, Team, FIELD_TL_X, FIELD_TL_Y, FIELD_HEIGHT, MatchManager, MatchState


def moving_circles(state):
    yield from state.players.values()
    yield state.ball


def step(state, clock, inputs, state_lock, send_cond, last_state_pickle):
    dt = clock.tick(60) / 1000.0  # Time since last frame

    with state_lock:
        prev_state = state.match_manager.state
        state.match_manager.update(dt)
        # Reset scores if match just ended (PLAYING -> BREAK)
        if prev_state == MatchState.PLAYING and state.match_manager.state == MatchState.BREAK:
            reset_scores(state)
            reset_ball(state)
            reset_players(state)

        if state.match_manager.state == MatchState.PLAYING:
            for address, player in state.players.items():
                if address in inputs:
                    apply_input(player, inputs[address])
                    del inputs[address]

            for circle in moving_circles(state):
                update_position(circle)

            handle_collisions(state)

            handle_kicks(state)

            check_goal(state)

        state.clock = pygame.time.get_ticks() // 1000

        data = pickle.dumps(state)
        last_state_pickle[:] = len(data).to_bytes(4, "big") + data

        with send_cond:
            send_cond.notify_all()

        clear_kicks(state)

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

    # Check for ball collision with field boundaries
    if state.ball.x < state.ball.radius + state.field_coords[0] and (state.ball.y < state.posts["tl"].y or state.ball.y > state.posts["bl"].y):
        state.ball.x = state.ball.radius + state.field_coords[0]
        state.ball.vx *= -1
    if state.ball.x >= state.field_coords[2] - state.ball.radius and (state.ball.y < state.posts["tr"].y or state.ball.y > state.posts["br"].y):
        state.ball.x = state.field_coords[2] - 1 - state.ball.radius
        state.ball.vx *= -1
    if state.ball.y < state.ball.radius + state.field_coords[1]:
        state.ball.y = state.ball.radius + state.field_coords[1]
        state.ball.vy *= -1
    if state.ball.y >= state.field_coords[3] - state.ball.radius:
        state.ball.y = state.field_coords[3] - 1 - state.ball.radius
        state.ball.vy *= -1

    # Check for player collision with player area boundaries
    for c in moving_circles(state): # state.players.values():
        if c.x < c.radius + state.player_area_coords[0]:
            c.x = c.radius + state.player_area_coords[0]
            c.vx *= -1
        if c.x >= state.player_area_coords[2] - c.radius:
            c.x = state.player_area_coords[2] - 1 - c.radius
            c.vx *= -1
        if c.y < c.radius + state.player_area_coords[1]:
            c.y = c.radius + state.player_area_coords[1]
            c.vy *= -1
        if c.y >= state.player_area_coords[3] - c.radius:
            c.y = state.player_area_coords[3] - 1 - c.radius
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
    MIN_KICK_FORCE = 1
    MAX_KICK_FORCE = 2.5
    DELTA_KICK_FORCE = MAX_KICK_FORCE - MIN_KICK_FORCE
    KICK_REACH = 20

    for player in state.players.values():
        if player.kick and not player.kick_locked:
            dx = state.ball.x - player.x
            dy = state.ball.y - player.y
            dist_sqr = dx**2 + dy**2

            if dist_sqr < (player.radius + state.ball.radius + KICK_REACH)**2:
                distance = math.sqrt(dist_sqr)

                # The closer it is, the stronger the kick
                proximity = distance - player.radius - state.ball.radius
                strength_factor = 1 - proximity / KICK_REACH
                kick_force = MIN_KICK_FORCE + DELTA_KICK_FORCE * strength_factor

                state.ball.vx += kick_force * dx / distance
                state.ball.vy += kick_force * dy / distance
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
        and state.posts["bl"].y > state.ball.y > state.posts["tl"].y
    ):
        # Blue team scores
        state.score_blue += 1
        reset_ball(state)
        reset_players(state)
    elif (
        state.ball.x > state.posts["tr"].x
        and state.posts["br"].y > state.ball.y > state.posts["tr"].y
    ):
        # Red team scores
        state.score_red += 1
        reset_ball(state)
        reset_players(state)


def reset_ball(state):
    state.ball.x = FIELD_TL_X + FIELD_WIDTH / 2
    state.ball.y = FIELD_TL_Y + FIELD_HEIGHT / 2
    state.ball.vx = 0
    state.ball.vy = 0


def reset_players(state):
    red_last = blue_last = PLAYER_AREA_TL_Y + PLAYER_AREA_HEIGHT / 2
    red_y_offset = blue_y_offset = 0
    red_side = blue_side = -1

    for player in state.players.values():
        if player.team == Team.RED:
            player.x = PLAYER_AREA_TL_X + 400
            player.y = red_last + red_y_offset * red_side
            red_last = player.y
            red_y_offset += 120
            red_side *= -1
        else:
            player.x = PLAYER_AREA_BR_X - 400
            player.y = blue_last + blue_y_offset * blue_side
            blue_last = player.y
            blue_y_offset += 120
            blue_side *= -1

        player.vx = 0
        player.vy = 0
        player.kick = False


def reset_scores(state):
    state.score_blue = 0
    state.score_red = 0

import argparse
import copy
import socketserver
import pygame
import pickle
import readline
import server_loop as loop
import uuid
from state import Player, State, SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_AREA_HEIGHT, PLAYER_AREA_TL_Y, PLAYER_AREA_BR_X, PLAYER_AREA_TL_X, Team, MatchManager
from threading import Condition, Lock, Thread
from hot_reloading import hot_cycle


state_lock = Lock()
send_cond = Condition()

clients = []
inputs = {}
last_state = [None]

state = State()


def main():
    parser = argparse.ArgumentParser(description="Haxball Game Client")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode with hot reloading.",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=12345, help="Server port (default: 12345)"
    )
    args = parser.parse_args()

    debug: bool = args.debug
    port: int = args.port

    pygame.init()

    clock = pygame.time.Clock()

    state.ball.x = SCREEN_WIDTH / 2
    state.ball.y = SCREEN_HEIGHT / 2

    game_cycle_thread = Thread(
        target=game_cycle,
        args=(debug, state, clock, inputs, state_lock, send_cond, last_state),
        daemon=True,
    )
    game_cycle_thread.start()

    interpreter_thread = Thread(target=interpreter, args=(state,), daemon=True)
    interpreter_thread.start()

    with socketserver.ThreadingTCPServer(("0.0.0.0", port), GameTCPHandler) as server:
        print("Server started, waiting for messages...")
        server.serve_forever()

    game_cycle_thread.join()
    interpreter_thread.join()


def game_cycle(debug, state, clock, inputs, state_lock, send_cond, last_state):
    if debug:
        # Debug mode
        print("Debug mode enabled. Hot reloading is active.")
        hot_cycle(
            loop.step, state, clock, inputs, state_lock, send_cond, last_state
        )
    else:
        # Normal mode
        while loop.step(state, clock, inputs, state_lock, send_cond, last_state):
            pass


def interpreter(state):
    while True:
        line = input(">>> ")
        if line.startswith("start_match"):
            state.match_manager.start_match()
        elif line.startswith("pause_match"):
            state.match_manager.pause_match()
            print("Match paused")
        elif line.startswith("resume_match"):
            state.match_manager.resume_match()
            print("Match resumed")
        elif line.startswith("set_match_time"):
            _, seconds = line.split()
            state.match_manager.set_match_time(int(seconds))
            print(f"Match time set to {seconds} seconds")
        elif line.startswith("set_break_time"):
            _, seconds = line.split()
            state.match_manager.set_break_time(int(seconds))
            print(f"Break time set to {seconds} seconds")
        else:
            exec(line)


MAX_NAME_ATTEMPTS = 3
MAX_TEAM_ATTEMPTS = 3


class GameTCPHandler(socketserver.BaseRequestHandler):
    def setup(self):
        # Assing player a unique ID
        self.player_id = str(uuid.uuid4())
        data_bytes = pickle.dumps(self.player_id)
        self.request.sendall(len(data_bytes).to_bytes(4, "big"))
        self.request.sendall(data_bytes)

        # Send teams and players to the client
        with state_lock:
            players_blue = [p.name for p in state.players.values() if p.team == Team.BLUE]
            players_red = [p.name for p in state.players.values() if p.team == Team.RED]

        data_to_send = {"teams": {"blue": players_blue, "red": players_red}}
        data_bytes = pickle.dumps(data_to_send)
        self.request.sendall(len(data_bytes).to_bytes(4, "big"))
        self.request.sendall(data_bytes)

        is_name_valid = False
        name_attempts = 0
        while not is_name_valid and name_attempts < MAX_NAME_ATTEMPTS:
            name_attempts += 1
            try:
                size = int.from_bytes(self.request.recv(4), "big")
                data = self.request.recv(size)
            except (ConnectionResetError, ConnectionAbortedError):
                return
            if not data:
                return

            name = pickle.loads(data)

            # Verifies submited name
            with state_lock:
                players_blue = [p.name for p in state.players.values() if p.team == Team.BLUE]
                players_red = [p.name for p in state.players.values() if p.team == Team.RED]
                all_players = players_blue + players_red
                is_name_valid = name not in all_players

            data_to_send = {'validity': is_name_valid}
            data_bytes = pickle.dumps(data_to_send)
            self.request.sendall(len(data_bytes).to_bytes(4, 'big'))
            self.request.sendall(data_bytes)

        if not is_name_valid:
            data_to_send = {'error': "Too many name input tries."}
            data_bytes = pickle.dumps(data_to_send)
            self.request.sendall(len(data_bytes).to_bytes(4, 'big'))
            self.request.sendall(data_bytes)
            return

        is_team_valid = False
        team_attempts = 0
        while not is_team_valid and team_attempts < MAX_TEAM_ATTEMPTS:
            team_attempts += 1
            try:
                size = int.from_bytes(self.request.recv(4), "big")
                data = self.request.recv(size)
            except (ConnectionResetError, ConnectionAbortedError):
                return
            if not data:
                return

            team = pickle.loads(data)

            # Verifies submited team
            with state_lock:
                number_players_blue = len([p.name for p in state.players.values() if p.team == Team.BLUE])
                number_players_red = len([p.name for p in state.players.values() if p.team == Team.RED])
                # Allow joining if the difference in team sizes would not exceed 1
                is_team_valid = abs((number_players_blue + (1 if team == Team.BLUE else 0)) - (number_players_red + (1 if team == Team.RED else 0))) <= 1

            data_to_send = {'validity': is_team_valid}
            data_bytes = pickle.dumps(data_to_send)
            self.request.sendall(len(data_bytes).to_bytes(4, 'big'))
            self.request.sendall(data_bytes)

        if not is_team_valid:
            data_to_send = {'error': "Too many team input tries."}
            data_bytes = pickle.dumps(data_to_send)
            self.request.sendall(len(data_bytes).to_bytes(4, 'big'))
            self.request.sendall(data_bytes)
            return

        print(f"{name} joined on team {team}")

        with state_lock:
            # Initialize position for new player
            if self.player_id not in state.players:
                if team == Team.RED:
                    state.players[self.player_id] = Player(name, team, PLAYER_AREA_TL_X + 45, PLAYER_AREA_TL_Y + PLAYER_AREA_HEIGHT / 2)
                else:
                    state.players[self.player_id] = Player(name, team, PLAYER_AREA_BR_X - 45, PLAYER_AREA_TL_Y + PLAYER_AREA_HEIGHT / 2)

            clients.append(self.request)

    def handle(self):
        while True:
            # Receive player's input
            try:
                size = int.from_bytes(self.request.recv(4), "big")
                data = self.request.recv(size)
            except (ConnectionResetError, ConnectionAbortedError):
                break

            if not data:
                break

            input = pickle.loads(data)
            window_width = input.window_width
            window_height = input.window_height
            inputs[self.player_id] = input

            with send_cond:
                send_cond.wait()
                default_size_state = copy.deepcopy(last_state[0])
                prepared_state = scale_and_offset_state(default_size_state, window_width, window_height)
                data = pickle.dumps(prepared_state)
                state_pickled = len(data).to_bytes(4, "big") + data
                self.request.sendall(state_pickled)

    def finish(self):
        with state_lock:
            if self.player_id in state.players:
                print(f"{state.players[self.player_id].name} left")
                # Remove client data on disconnect
                if self.request in clients:
                    clients.remove(self.request)
                if self.player_id in state.players:
                    del state.players[self.player_id]
                if self.player_id in inputs:
                    del inputs[self.player_id]


def scale_and_offset_state(default_size_state, window_width, window_height):
    scale_ratio = min(window_height / SCREEN_HEIGHT, window_width / SCREEN_WIDTH)

    field_x1 = default_size_state.field_coords[0] * scale_ratio
    field_y1 = default_size_state.field_coords[1] * scale_ratio
    field_x2 = default_size_state.field_coords[2] * scale_ratio
    field_y2 = default_size_state.field_coords[3] * scale_ratio

    field_width = field_x2 - field_x1
    field_height = field_y2 - field_y1

    offset_x = (window_width - field_width) / 2 - field_x1
    offset_y = (window_height - field_height) / 2 - field_y1

    # Adjust players, ball, and posts coordinates and radii
    for player in default_size_state.players.values():
        scale_and_offset_circle(player, scale_ratio, offset_x, offset_y)
    scale_and_offset_circle(default_size_state.ball, scale_ratio, offset_x, offset_y)
    for post in default_size_state.posts.values():
        scale_and_offset_circle(post, scale_ratio, offset_x, offset_y)

    # Adjust field coordinates
    default_size_state.field_coords = (
        round(field_x1 + offset_x),
        round(field_y1 + offset_y),
        round(field_x2 + offset_x),
        round(field_y2 + offset_y),
    )

    return default_size_state


def scale_and_offset_circle(circle, scale_ratio, offset_x, offset_y):
    circle.x = round(circle.x * scale_ratio + offset_x)
    circle.y = round(circle.y * scale_ratio + offset_y)
    circle.radius = round(circle.radius * scale_ratio)


if __name__ == "__main__":
    main()

import argparse
import socketserver
import pygame
import pickle
import readline
import server_loop as loop
from state import Player, State, SCREEN_WIDTH, SCREEN_HEIGHT, Team
from threading import Condition, Lock, Thread
from hot_reloading import hot_cycle


state_lock = Lock()
send_cond = Condition()

clients = []
inputs = {}
last_state_pickle = bytearray()

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
        args=(debug, state, clock, inputs, state_lock, send_cond, last_state_pickle),
        daemon=True,
    )
    game_cycle_thread.start()

    interpreter_thread = Thread(target=interpreter, daemon=True)
    interpreter_thread.start()

    with socketserver.ThreadingTCPServer(("0.0.0.0", port), GameTCPHandler) as server:
        print("Server started, waiting for messages...")
        server.serve_forever()

    game_cycle_thread.join()
    interpreter_thread.join()


def game_cycle(debug, state, clock, inputs, state_lock, send_cond, last_state_pickle):
    if debug:
        # Debug mode
        print("Debug mode enabled. Hot reloading is active.")
        hot_cycle(
            loop.step, state, clock, inputs, state_lock, send_cond, last_state_pickle
        )
    else:
        # Normal mode
        while loop.step(state, clock, inputs, state_lock, send_cond, last_state_pickle):
            pass


def interpreter():
    while True:
        line = input(">>> ")
        exec(line)


class GameTCPHandler(socketserver.BaseRequestHandler):
    def setup(self):
        try:
            size = int.from_bytes(self.request.recv(4), "big")
            data = self.request.recv(size)
        except (ConnectionResetError, ConnectionAbortedError):
            return
        if not data:
            return

        name = pickle.loads(data)

        try:
            size = int.from_bytes(self.request.recv(4), "big")
            data = self.request.recv(size)
        except (ConnectionResetError, ConnectionAbortedError):
            return
        if not data:
            return

        team = pickle.loads(data)

        print(f"{name} joined on team {team}")

        with state_lock:
            # Initialize position for new player
            if self.client_address not in state.players:
                if team == Team.RED:
                    state.players[self.client_address] = Player(name, team, 45, SCREEN_HEIGHT / 2)
                else:
                    state.players[self.client_address] = Player(name, team, SCREEN_WIDTH - 45, SCREEN_HEIGHT / 2)

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

            inputs[self.client_address] = input

            with send_cond:
                send_cond.wait()
                self.request.sendall(last_state_pickle)

    def finish(self):
        print(f"{state.players[self.client_address].name} left")
        with state_lock:
            # Remove client data on disconnect
            if self.request in clients:
                clients.remove(self.request)
            if self.client_address in state.players:
                del state.players[self.client_address]


if __name__ == "__main__":
    main()

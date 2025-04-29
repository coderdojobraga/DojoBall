import socketserver
import pygame
import pickle
import readline
import server_loop
from threading import Condition, Lock, Thread
from state import Player, State
from hot_reloading import hot_cycle


pygame.init()  # Ensure pygame is initialized

clock = pygame.time.Clock()

state = State()
state.ball.x = 400
state.ball.y = 400
state_lock = Lock()  # Lock to ensure thread-safe access to shared state

SCREEN_WIDTH = 720
SCREEN_HEIGHT = 720

last_state_pickle = bytearray()
clients = []
inputs = {}
running = True
send_cond = Condition()


def game_cycle():
    global running
    global last_state_pickle

    hot_cycle(server_loop.step, state, clock, inputs, state_lock, send_cond, last_state_pickle)


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
                state.players[self.client_address] = Player(name, team, 360, 360)

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


def interpreter():
    while True:
        line = input(">>> ")
        exec(line)


if __name__ == "__main__":
    game_cycle_thread = Thread(target=game_cycle, daemon=True)
    game_cycle_thread.start()

    interpreter_thread = Thread(target=interpreter, daemon=True)
    interpreter_thread.start()

    with socketserver.ThreadingTCPServer(('0.0.0.0', 12345), GameTCPHandler) as server:
        print("Server started, waiting for messages...")
        server.serve_forever()

    game_cycle_thread.join()
    interpreter_thread.join()

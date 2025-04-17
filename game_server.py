import socketserver
import pygame
import pickle
import math
from threading import Lock, Thread
from state import Player, State


pygame.init()  # Ensure pygame is initialized

clock = pygame.time.Clock()
clock1 = pygame.time.Clock()

state = State()
state.ball.x = 400
state.ball.y = 400
state_lock = Lock()  # Lock to ensure thread-safe access to shared state

SCREEN_WIDTH = 720
SCREEN_HEIGHT = 720

clients = []

running = True


def game_cycle():
    global running

    while running:
        # print(clock.get_fps())

        with state_lock:
            for player in state.players.values():
                player.update_position()

            state.ball.update_position()

            state.handle_collisions()

            state.handle_kicks()

            data = pickle.dumps(state)
            for client in clients:
                client.sendall(len(data).to_bytes(4, "big") + data)

            state.clear_kicks()

        clock.tick(60)


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

            x = (-1 if input.left else 0) + (1 if input.right else 0)
            y = (-1 if input.up else 0) + (1 if input.down else 0)

            if x or y:
                move_magnitude = math.sqrt(x ** 2 + y ** 2)
                mx = x / move_magnitude
                my = y / move_magnitude

                with state_lock:
                    p = state.players[self.client_address]

                    if input.kick:
                        p.vx += 0.05 * 0.7 * mx
                        p.vy += 0.05 * 0.7 * my
                    else:
                        p.vx += 0.05 * mx
                        p.vy += 0.05 * my

                    # Normalize velocity to ensure norm is 1
                    magnitude = math.sqrt(p.vx ** 2 + p.vy ** 2)
                    if magnitude > 1:
                        p.vx /= magnitude
                        p.vy /= magnitude

            if input.kick:
                with state_lock:
                    p = state.players[self.client_address]
                    p.kick = True


    def finish(self):
        print(f"{state.players[self.client_address].name} left")
        with state_lock:
            # Remove client data on disconnect
            if self.request in clients:
                clients.remove(self.request)
            if self.client_address in state.players:
                del state.players[self.client_address]


if __name__ == "__main__":
    game_cycle_thread = Thread(target=game_cycle, daemon=True)
    game_cycle_thread.start()

    with socketserver.ThreadingTCPServer(('0.0.0.0', 12345), GameTCPHandler) as server:
        print("Server started, waiting for messages...")
        server.serve_forever()

    game_cycle_thread.join()

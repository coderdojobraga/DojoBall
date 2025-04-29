import argparse
import pygame
import socket
import client_loop as loop
from client_loop import send_data
from state import Team
from pygments.lexers.python import PythonTracebackLexer
from pygments.formatters import Terminal256Formatter
from hot_reloading import hot_cycle


lexer = PythonTracebackLexer(stripall=True)
formatter = Terminal256Formatter(style="default")


def main():
    parser = argparse.ArgumentParser(description="Haxball Game Client")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode with hot reloading.")
    parser.add_argument("-H", "--host", type=str, default="127.0.0.1", help="Server IP address (default: 127.0.0.1)")
    parser.add_argument("-p", "--port", type=int, default=12345, help="Server port (default: 12345)")
    args = parser.parse_args()

    debug: bool = args.debug
    host: str = args.host
    port: int = args.port

    # Criar socket TCP
    client_socket = socket.create_connection((host, port))

    # Ler nome
    name = input("Nick: ")

    # Enviar nome
    send_data(client_socket, name)

    # Ler equipa
    while True:
        team_input = input("Team ([b]lue/[r]ed): ").strip().lower()

        match team_input:
            case "[b]lue" | "blue" | "b":
                team = Team.BLUE
            case "[r]ed" | "red" | "r":
                team = Team.RED
            case _:
                print("Invalid team. Please choose '[b]lue' or '[r]ed'.")
                continue

        break

    # Enviar equipa
    send_data(client_socket, team)

    # Iniciar pygame
    pygame.init()

    # Pygame setup
    screen = pygame.display.set_mode((720, 720))
    name_font = pygame.font.SysFont("arial", 30)
    transparent_surface = pygame.Surface((720, 720), pygame.SRCALPHA)

    if debug:
        # Debug mode
        print("Debug mode enabled. Hot reloading is active.")
        hot_cycle(loop.step, client_socket, screen, transparent_surface, name_font)
    else:
        # Normal mode
        while loop.step(client_socket, screen, transparent_surface, name_font):
            pass

    client_socket.close()
    pygame.quit()


if __name__ == "__main__":
    main()

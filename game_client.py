import pygame
import socket
import loop
from state import Team
from loop import send_data
from pygments.lexers.python import PythonTracebackLexer
from pygments.formatters import Terminal256Formatter
from hot_reloading import hot_cycle

lexer = PythonTracebackLexer(stripall=True)
formatter = Terminal256Formatter(style="default")


def main():
    # Criar socket TCP
    client_socket = socket.create_connection(('127.0.0.1', 12345))

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

    hot_cycle(loop.step, client_socket, screen, transparent_surface, name_font)

    client_socket.close()
    pygame.quit()


if __name__ == "__main__":
    main()

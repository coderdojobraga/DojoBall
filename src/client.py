import argparse
import pygame
import socket
import client_loop as loop
from client_loop import send_data, receive_data
from state import Team, SCREEN_WIDTH, SCREEN_HEIGHT
from hot_reloading import hot_cycle

class TooManyTriesError(Exception):
    """Exceção lançada quando há demasiadas tentativas inválidas de nome/equipa."""
    pass

def initial_configuration(client_socket):
    # Receive player ID from server
    try:
        player_id = receive_data(client_socket)
    except (ConnectionResetError, ConnectionAbortedError):
        print("Error receiving player ID from server.")
        return None

    # Receber equipas e jogadores do servidor
    try:
        initial_info = receive_data(client_socket)
    except (ConnectionResetError, ConnectionAbortedError):
        print("Error receiving initial information from server.")
        return

    print("Current teams:")
    print("  Blue team:")
    for player in initial_info["teams"]["blue"]:
        print(f"    - {player}")
    print("  Red team:")
    for player in initial_info["teams"]["red"]:
        print(f"    - {player}")

    is_name_valid = False
    while not is_name_valid:

        # Ler nome
        name = input("Nick: ")

        # Enviar nome
        send_data(client_socket, name)

        try:
            name_info = receive_data(client_socket)
        except (ConnectionResetError, ConnectionAbortedError):
            print("Error receiving initial information from server.")
            return

        if name_info.get("error", False):
            print(name_info["error"])
            raise TooManyTriesError()

        is_name_valid = name_info["validity"]

        if not is_name_valid:
            print("The player name is already choosen. Please type another one.")

    is_team_valid = False
    while not is_team_valid:

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

        try:
            team_info = receive_data(client_socket)
        except (ConnectionResetError, ConnectionAbortedError):
            print("Error receiving initial information from server.")
            return

        if team_info.get("error", False):
            print(team_info["error"])
            raise TooManyTriesError()

        is_team_valid = team_info["validity"]

        if not is_team_valid:
            print("This team can't be choosen. Please type another one.")

    return player_id, name


def main():
    parser = argparse.ArgumentParser(description="Haxball Game Client")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode with hot reloading.",
    )
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="127.0.0.1",
        help="Server IP address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=4005, help="Server port (default: 12345)"
    )
    args = parser.parse_args()

    debug: bool = args.debug
    host: str = args.host
    port: int = args.port

    # Criar socket TCP
    client_socket = socket.create_connection((host, port))

    try:
        # Ver equipas e jogadores, escolher o nome e equipa
        player_id, name = initial_configuration(client_socket)
        if player_id is None:
            return

        # Iniciar pygame
        pygame.init()

        # Pygame setup
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        name_font = pygame.font.SysFont("arial", 30)
        transparent_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        if debug:
            # Debug mode
            print("Debug mode enabled. Hot reloading is active.")
            hot_cycle(loop.step, client_socket, screen, transparent_surface, name_font, player_id, name)
        else:
            # Normal mode
            while loop.step(client_socket, screen, transparent_surface, name_font, player_id, name):
                pass

        client_socket.close()
        pygame.quit()
    except TooManyTriesError:
        client_socket.close()


if __name__ == "__main__":
    main()

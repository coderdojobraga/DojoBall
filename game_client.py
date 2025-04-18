import pygame
import socket
import os
import loop
import shutil
import traceback
from state import Team
from importlib import reload
from loop import send_data
from pygments.lexers.python import PythonTracebackLexer
from pygments.formatters import Terminal256Formatter
from pygments import highlight


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

    running = True

    last_mtime = os.stat("loop.py").st_mtime
    shutil.copyfile("loop.py", ".loop_backup")

    # Ciclo do jogo
    while running:
        current_mtime = os.stat("loop.py").st_mtime

        if current_mtime > last_mtime:
            last_mtime = current_mtime
            try:
                reload(loop)
                print("loop module reloaded")
                try:
                    running = loop.step(client_socket, screen, transparent_surface, name_font)
                    shutil.copyfile("loop.py", ".loop_backup")
                    continue
                except Exception as e:
                    print("Error in game loop:\n")
                    print(highlight(traceback.format_exc(), lexer, formatter))
                    shutil.copyfile("loop.py", ".loop_error")
                    shutil.copyfile(".loop_backup", "loop.py")
                    reload(loop)
                    shutil.copyfile(".loop_error", "loop.py")
                    last_mtime = os.stat("loop.py").st_mtime
            except Exception as e:
                print("Error reloading loop module:\n")
                print(highlight(traceback.format_exc(), lexer, formatter))

        running = loop.step(client_socket, screen, transparent_surface, name_font)

    client_socket.close()
    pygame.quit()


if __name__ == "__main__":
    main()

# if touch
#   if reload
#     if run
#       backup
#     else
#       fix
#   else
#     run
# else
#   run
# 
# 
# if touch
#   if reload
#     if run
#       backup
#     else
#       fix
#     continue
# run
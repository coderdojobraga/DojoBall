import pygame
import pygame.gfxdraw
import socket
import pickle
from input import Input
from state import Team


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
            case "blue" | "b":
                team = Team.BLUE
            case "red" | "r":
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

    # Ciclo do jogo
    while running:
        # Boilerplate para eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Ler input
        inputs = get_input(pygame.key.get_pressed())

        # Enviar input para o servidor
        send_data(client_socket, inputs)

        # Receber estado atualizado do servidor
        state = receive_data(client_socket)

        # Desenhar o estado
        render(state, screen, transparent_surface, name_font, client_socket.getsockname())

    client_socket.close()
    pygame.quit()


def send_data(client_socket, data):
    data = pickle.dumps(data)
    data = len(data).to_bytes(4, "big") + data
    client_socket.sendall(data)


def receive_data(client_socket):
    size = int.from_bytes(client_socket.recv(4), "big")
    data = bytearray()
    while len(data) < size:
        chunk = client_socket.recv(size - len(data))
        data.extend(chunk)
    return pickle.loads(data)


def get_input(keys):
    input = Input()

    input.up = keys[pygame.K_w]
    input.down = keys[pygame.K_s]
    input.left = keys[pygame.K_a]
    input.right = keys[pygame.K_d]
    input.kick = keys[pygame.K_SPACE]

    return input


def render(state, screen, transparent_surface, name_font, sockname):
    # Desenhar fundo
    transparent_surface.fill((0, 0, 0, 0))
    screen.fill("#729861")

    # Desenhar a bola
    draw_ball(state.ball, screen)

    # Desenhar o jogador local
    draw_myself(state.players.pop(sockname), screen, transparent_surface)

    # Desenhar os outros jogadores
    for p in state.players.values():
        playerName = name_font.render(p.name, True, (255, 255, 255))
        screen.blit(playerName, (p.x - playerName.get_rect().width / 2, p.y + 50))
        draw_player(p, screen)

    # Atualizar o ecra
    screen.blit(transparent_surface, (0, 0))
    pygame.display.flip()


def draw_ball(ball, screen):
    x = int(ball.x)
    y = int(ball.y)
    pygame.gfxdraw.filled_circle(screen, x, y, 30, pygame.Color("black"))
    pygame.gfxdraw.aacircle(screen, x, y, 30, pygame.Color("black"))
    pygame.gfxdraw.filled_circle(screen, x, y, 25, pygame.Color("white"))
    pygame.gfxdraw.aacircle(screen, x, y, 25, pygame.Color("white"))


def draw_myself(me, screen, transparent_surface):
    draw_player(me, screen)
    x = int(me.x)
    y = int(me.y)
    pygame.draw.circle(transparent_surface, pygame.Color(200, 200, 200, 100), (me.x, me.y), 70, 5)
    pygame.gfxdraw.aacircle(screen, x, y, 65, pygame.Color(200, 200, 200, 100))
    pygame.gfxdraw.aacircle(screen, x, y, 70, pygame.Color(200, 200, 200, 100))


def draw_player(p, screen):
    border_color = pygame.Color("white") if p.kick else pygame.Color("black")
    inner_color = pygame.Color("#5688e4") if p.team == Team.BLUE else pygame.Color("#e46f56")

    x = int(p.x)
    y = int(p.y)

    # Draw the outer border
    pygame.gfxdraw.filled_circle(screen, x, y, 45, border_color)
    pygame.gfxdraw.aacircle(screen, x, y, 45, border_color)

    # Draw the inner circle
    pygame.gfxdraw.filled_circle(screen, x, y, 40, inner_color)
    pygame.gfxdraw.aacircle(screen, x, y, 40, inner_color)


if __name__ == "__main__":
    main()

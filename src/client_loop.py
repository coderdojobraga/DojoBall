import pygame
import pygame.gfxdraw
import pickle
from input import Input
from state import Team


COLOR_FIELD = pygame.Color("#729861")
COLOR_TEAM_BLUE = pygame.Color("#5688e4")
COLOR_TEAM_RED = pygame.Color("#e46f56")
COLOR_BORDER = pygame.Color("black")
COLOR_BORDER_KICK = pygame.Color("white")
COLOR_KICK_RANGE = pygame.Color(200, 200, 200, 100)


def step(client_socket, screen, transparent_surface, name_font):
    # Boilerplate para eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

    # Ler input
    inputs = get_input(pygame.key.get_pressed())

    # Enviar input para o servidor
    send_data(client_socket, inputs)

    # Receber estado atualizado do servidor
    state = receive_data(client_socket)

    # Desenhar o estado
    render(state, screen, transparent_surface, name_font, client_socket.getsockname())

    return True


def send_data(client_socket, data):
    data = pickle.dumps(data)
    data = len(data).to_bytes(4) + data
    client_socket.sendall(data)


def receive_data(client_socket):
    size = int.from_bytes(client_socket.recv(4))
    data = bytearray()
    while len(data) < size:
        chunk = client_socket.recv(size - len(data))
        data.extend(chunk)
    return pickle.loads(data)


def get_input(keys):
    return Input(
        keys[pygame.K_w],
        keys[pygame.K_s],
        keys[pygame.K_a],
        keys[pygame.K_d],
        keys[pygame.K_SPACE],
    )


def render(state, screen, transparent_surface, name_font, sockname):
    # Desenhar fundo
    transparent_surface.fill((0, 0, 0, 0))
    screen.fill(COLOR_FIELD)

    # Desenhar a bola
    draw_ball(state.ball, screen)

    # Desenhar o jogador local
    draw_myself(state.players.pop(sockname), screen, transparent_surface)

    # Desenhar os outros jogadores
    for player in state.players.values():
        draw_player(player, screen)
        draw_name(player, screen, name_font)

    # Desenhar postes
    for post in state.posts.values():
        draw_post(screen, post)

    draw_scoreboard(state, screen)

    draw_timer(state.timer, screen)

    # Atualizar o ecra
    screen.blit(transparent_surface, (0, 0))
    pygame.display.flip()


def draw_ball(ball, screen):
    x = int(ball.x)
    y = int(ball.y)

    border_radius = round(ball.radius)
    inner_radius = int(ball.radius * 0.84)

    # Desenhar borda
    pygame.gfxdraw.filled_circle(screen, x, y, border_radius, pygame.Color("black"))
    pygame.gfxdraw.aacircle(screen, x, y, border_radius, pygame.Color("black"))

    # Desenhar circulo interior
    pygame.gfxdraw.filled_circle(screen, x, y, inner_radius, pygame.Color("white"))
    pygame.gfxdraw.aacircle(screen, x, y, inner_radius, pygame.Color("white"))


def draw_myself(player, screen, transparent_surface):
    draw_player(player, screen)

    # Obter a posição do jogador
    pos = x, y = int(player.x), int(player.y)

    # Calcular dimensões do indicador de pontapé
    inner_radius = round(1.44 * player.radius)
    outer_radius = round(1.56 * player.radius)
    thickness = outer_radius - inner_radius

    # Desenhar indicador do alcance de pontapé
    pygame.draw.circle(
        transparent_surface, COLOR_KICK_RANGE, pos, outer_radius, thickness
    )
    pygame.gfxdraw.aacircle(screen, x, y, inner_radius, COLOR_KICK_RANGE)
    pygame.gfxdraw.aacircle(screen, x, y, outer_radius, COLOR_KICK_RANGE)


def draw_player(player, screen):
    border_color = COLOR_BORDER_KICK if player.kick else COLOR_BORDER
    inner_color = COLOR_TEAM_BLUE if player.team == Team.BLUE else COLOR_TEAM_RED

    # Obter a posição do jogador
    x = int(player.x)
    y = int(player.y)

    border_radius = player.radius
    inner_radius = round(0.9 * player.radius)

    # Desenhar borda
    pygame.gfxdraw.filled_circle(screen, x, y, border_radius, border_color)
    pygame.gfxdraw.aacircle(screen, x, y, border_radius, border_color)

    # Desenhar circulo interior
    pygame.gfxdraw.filled_circle(screen, x, y, inner_radius, inner_color)
    pygame.gfxdraw.aacircle(screen, x, y, inner_radius, inner_color)


def draw_name(player, screen, name_font):
    playerName = name_font.render(player.name, True, (255, 255, 255))
    screen.blit(playerName, (player.x - playerName.get_rect().width / 2, player.y + 50))


def draw_post(screen, post):
    inner_color = COLOR_TEAM_BLUE if post.team == Team.BLUE else COLOR_TEAM_RED

    x = int(post.x)
    y = int(post.y)

    border_radius = int(post.radius)
    inner_radius = round(0.75 * post.radius)

    # Desenhar borda
    pygame.gfxdraw.filled_circle(screen, x, y, border_radius, COLOR_BORDER)
    pygame.gfxdraw.aacircle(screen, x, y, border_radius, COLOR_BORDER)

    # Desenhar circulo interior
    pygame.gfxdraw.filled_circle(screen, x, y, inner_radius, inner_color)
    pygame.gfxdraw.aacircle(screen, x, y, inner_radius, inner_color)


def draw_scoreboard(state, screen):
    font = pygame.font.SysFont("arial", 30)
    red_score_text = font.render(
        f"Blue: {state.score_red}", True, pygame.Color("white")
    )
    blue_score_text = font.render(
        f"Red: {state.score_blue}", True, pygame.Color("white")
    )

    screen.blit(blue_score_text, (50, 50))
    screen.blit(red_score_text, (1080 - blue_score_text.get_width() - 50, 50))

def draw_timer(timer, screen):
    font = pygame.font.SysFont("arial", 30)
    timer_text = font.render(f"{timer // 60:02d}:{timer % 60:02d}", True, pygame.Color("white"))
    screen.blit(timer_text, (540 - timer_text.get_width() // 2, 50))

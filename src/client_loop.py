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

    draw_hud(screen, state)

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


def draw_hud(screen, state):
    font = pygame.font.SysFont("Arial Bold", 33)

    border_radius = 5
    team_rect_size = 23
    score_width = 35
    hyphen_width = 6.67
    colon_width = 6.67
    hud_height = 35
    hud_width = 442.73
    hud_padding = 5
    clock_digit_width = 15

    hud_pos_x = screen.get_width() / 2 - hud_width / 2
    hud_pos_y = 0
    hud_pos_end_x = hud_pos_x + hud_width
    team_rect_pos_y = (hud_height - team_rect_size) / 2
    font_pos_y = (hud_height - font.get_height()) / 2 + 2

    hud_background = pygame.Rect(hud_pos_x, hud_pos_y, hud_width, hud_height)
    pygame.draw.rect(screen, "#1b2025", hud_background, border_bottom_left_radius=border_radius, border_bottom_right_radius=border_radius)

    red_rect_pos = hud_pos_x + hud_padding
    red_rect = pygame.Rect(red_rect_pos, team_rect_pos_y, team_rect_size, team_rect_size)
    pygame.draw.rect(screen, COLOR_TEAM_RED, red_rect, border_radius=border_radius)

    score_red = font.render(f"{state.score_red}", True, pygame.Color("white"))
    score_red_pos = red_rect_pos + team_rect_size
    screen.blit(score_red, (score_red_pos + (score_width - score_red.get_width()) / 2, font_pos_y))

    score_hyphen = font.render("-", True, pygame.Color("white"))
    score_hyphen_pos = score_red_pos + score_width + (hyphen_width - score_hyphen.get_width()) / 2
    screen.blit(score_hyphen, (score_hyphen_pos, font_pos_y))

    score_blue = font.render(f"{state.score_blue}", True, pygame.Color("white"))
    score_blue_pos = score_red_pos + score_width + hyphen_width
    screen.blit(score_blue, (score_blue_pos + (score_width - score_blue.get_width()) / 2, font_pos_y))

    blue_rect_pos = score_blue_pos + score_width
    blue_rect = pygame.Rect(blue_rect_pos, team_rect_pos_y, team_rect_size, team_rect_size)
    pygame.draw.rect(screen, COLOR_TEAM_BLUE, blue_rect, border_radius=border_radius)

    clock_sec_ones_pos_end = hud_pos_end_x - hud_padding

    clock_sec_ones = font.render(f"{state.clock % 60 % 10}", True, pygame.Color("white"))
    clock_sec_ones_pos = clock_sec_ones_pos_end - clock_digit_width
    screen.blit(clock_sec_ones, (clock_sec_ones_pos + (clock_digit_width - clock_sec_ones.get_width()) / 2, font_pos_y))

    clock_sec_tens = font.render(f"{state.clock % 60 // 10}", True, pygame.Color("white"))
    clock_sec_tens_pos = clock_sec_ones_pos - clock_digit_width
    screen.blit(clock_sec_tens, (clock_sec_tens_pos + (clock_digit_width - clock_sec_tens.get_width()) / 2, font_pos_y))

    clock_colon = font.render(":", True, pygame.Color("white"))
    clock_colon_pos = clock_sec_tens_pos - colon_width
    screen.blit(clock_colon, (clock_colon_pos + (colon_width - clock_colon.get_width()) / 2, font_pos_y))

    clock_min_ones = font.render(f"{state.clock // 60 % 10}", True, pygame.Color("white"))
    clock_min_ones_pos = clock_colon_pos - clock_digit_width
    screen.blit(clock_min_ones, (clock_min_ones_pos + (clock_digit_width - clock_min_ones.get_width()) / 2, font_pos_y))

    clock_min_tens = font.render(f"{state.clock // 600}", True, pygame.Color("white"))
    clock_min_tens_pos = clock_min_ones_pos - clock_digit_width
    screen.blit(clock_min_tens, (clock_min_tens_pos + (clock_digit_width - clock_min_tens.get_width()) / 2, font_pos_y))

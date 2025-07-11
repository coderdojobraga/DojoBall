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


def step(client_socket, screen, transparent_surface, name_font, player_id, name):
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
    render(state, screen, transparent_surface, name_font, player_id)

    return True


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
    return Input(
        keys[pygame.K_w],
        keys[pygame.K_s],
        keys[pygame.K_a],
        keys[pygame.K_d],
        keys[pygame.K_SPACE],
        pygame.display.get_window_size()[0],
        pygame.display.get_window_size()[1],
    )


def render(state, screen, transparent_surface, name_font, player_id):
    # Desenhar fundo
    transparent_surface.fill((0, 0, 0, 0))
    screen.fill(COLOR_FIELD)

    draw_field(screen, state.field_coords)

    # Desenhar a bola
    draw_ball(state.ball, screen)

    # Desenhar o jogador local
    if player_id in state.players:
        draw_myself(state.players.pop(player_id), screen, transparent_surface)

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


def draw_field(screen, field_coords):
    x1, y1, x2, y2 = field_coords
    pygame.draw.rect(screen, pygame.Color("#688e57"), (x1, y1, x2-x1, y2-y1))
    pygame.draw.rect(screen, pygame.Color("#c6e7bd"), (x1, y1, x2-x1, y2-y1), width=7)


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
    font = pygame.font.SysFont(["Arial Black", "Arial Bold", "Gadget", "sans-serif"], 33, bold=False)

    # Cores
    font_color = pygame.Color("#fefeff")
    hud_background_color = pygame.Color("#1b2025")

    # Dimensões
    border_radius = 5
    team_rect_size = 23
    score_width = 35
    hyphen_width = 7
    colon_width = 7
    hud_height = 35
    hud_width = 443
    hud_padding = 5
    clock_digit_width = 15

    # Posições de ancoragem
    hud_pos_x = round((screen.get_width() - hud_width) / 2)
    hud_pos_y = 0
    team_rect_pos_y = round((hud_height - team_rect_size) / 2)
    font_pos_y = round((hud_height - font.get_height()) / 2) + 2
    clock_end = hud_pos_x + hud_width - hud_padding

    # Desenhar fundo do HUD
    hud_background = pygame.Rect(hud_pos_x, hud_pos_y, hud_width, hud_height)
    pygame.draw.rect(screen, hud_background_color, hud_background, border_bottom_left_radius=border_radius, border_bottom_right_radius=border_radius)

    # Desenhar retângulo da equipa vermelha
    red_rect_pos = hud_pos_x + hud_padding
    red_rect = pygame.Rect(red_rect_pos, team_rect_pos_y, team_rect_size, team_rect_size)
    pygame.draw.rect(screen, COLOR_TEAM_RED, red_rect, border_radius=border_radius)

    # Desenhar pontuação da equipa vermelha
    score_red = font.render(f"{state.score_red}", True, font_color)
    score_red_pos = red_rect_pos + team_rect_size
    screen.blit(score_red, (score_red_pos + round((score_width - score_red.get_width()) / 2), font_pos_y))

    # Desenhar hífen entre pontuações
    score_hyphen = font.render("-", True, font_color)
    score_hyphen_pos = score_red_pos + score_width + round((hyphen_width - score_hyphen.get_width()) / 2)
    screen.blit(score_hyphen, (score_hyphen_pos, font_pos_y))

    # Desenhar pontuação da equipa azul
    score_blue = font.render(f"{state.score_blue}", True, font_color)
    score_blue_pos = score_red_pos + score_width + hyphen_width
    screen.blit(score_blue, (score_blue_pos + round((score_width - score_blue.get_width()) / 2), font_pos_y))

    # Desenhar retângulo da equipa azul
    blue_rect_pos = score_blue_pos + score_width
    blue_rect = pygame.Rect(blue_rect_pos, team_rect_pos_y, team_rect_size, team_rect_size)
    pygame.draw.rect(screen, COLOR_TEAM_BLUE, blue_rect, border_radius=border_radius)

    # Desenhar unidade dos segundos do relógio
    clock_sec_ones = font.render(f"{state.clock % 60 % 10}", True, font_color)
    clock_sec_ones_pos = clock_end - clock_digit_width
    screen.blit(clock_sec_ones, (clock_sec_ones_pos + round((clock_digit_width - clock_sec_ones.get_width()) / 2), font_pos_y))

    # Desenhar dezenas dos segundos do relógio
    clock_sec_tens = font.render(f"{state.clock % 60 // 10}", True, font_color)
    clock_sec_tens_pos = clock_sec_ones_pos - clock_digit_width
    screen.blit(clock_sec_tens, (clock_sec_tens_pos + round((clock_digit_width - clock_sec_tens.get_width()) / 2), font_pos_y))

    # Desenhar dois pontos do relógio
    clock_colon = font.render(":", True, font_color)
    clock_colon_pos = clock_sec_tens_pos - colon_width
    screen.blit(clock_colon, (clock_colon_pos + round((colon_width - clock_colon.get_width()) / 2), font_pos_y))

    # Desenhar unidade dos minutos do relógio
    clock_min_ones = font.render(f"{state.clock // 60 % 10}", True, font_color)
    clock_min_ones_pos = clock_colon_pos - clock_digit_width
    screen.blit(clock_min_ones, (clock_min_ones_pos + round((clock_digit_width - clock_min_ones.get_width()) / 2), font_pos_y))

    # Desenhar dezenas dos minutos do relógio
    clock_min_tens = font.render(f"{state.clock // 600}", True, font_color)
    clock_min_tens_pos = clock_min_ones_pos - clock_digit_width
    screen.blit(clock_min_tens, (clock_min_tens_pos + round((clock_digit_width - clock_min_tens.get_width()) / 2), font_pos_y))

    # Desenhar estado da partida
    minutes = int(state.match_manager.time_remaining) // 60
    seconds = int(state.match_manager.time_remaining) % 60
    match_state_text = f"{state.match_manager.state.name.capitalize()}: {minutes:02d}:{seconds:02d}"
    match_state_surface = font.render(match_state_text, True, font_color)

    # Calcular a posição central do HUD
    hud_center_x = hud_pos_x + hud_width / 2
    text_width = match_state_surface.get_width()

    # Ajustar a posição do texto para centralizar
    text_pos_x = hud_center_x - text_width / 2
    text_pos_y = font_pos_y

    screen.blit(match_state_surface, (text_pos_x, text_pos_y))

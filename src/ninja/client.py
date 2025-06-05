import pygame
import socket
import pickle
from input import Input
from state import Team


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


# Criar socket
client_socket = socket.create_connection(("127.0.0.1", 12345))

# Ler nome
name = input("Nick: ")

# Enviar nome
send_data(client_socket, name)

# Ler equipa
team_input = input("Equipa (azul/vermelha): ")

# Enviar equipa
if team_input == "azul":
    send_data(client_socket, Team.BLUE)
else:
    send_data(client_socket, Team.RED)

# Iniciar pygame
pygame.init()

# Iniciar ecra
screen = pygame.display.set_mode((720, 720))

running = True

# Ciclo do jogo
while running:
    # Boilerplate para eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Ler teclas pressionadas
    keys = pygame.key.get_pressed()

    # Iniciar estrutura de input
    inputs = Input(
        keys[pygame.K_w],
        keys[pygame.K_s],
        keys[pygame.K_a],
        keys[pygame.K_d],
        keys[pygame.K_SPACE],
    )

    # Enviar input para o servidor
    send_data(client_socket, inputs)

    # Receber estado atualizado do servidor
    state = receive_data(client_socket)

    # Desenhar fundo
    screen.fill("green")

    # Desenhar bola
    pygame.draw.circle(screen, pygame.Color("white"), (state.ball.x, state.ball.y), 30)

    # Desenhar jogadores
    for player in state.players.values():
        if player.team == Team.BLUE:
            pygame.draw.circle(screen, pygame.Color("yellow"), (player.x, player.y), 45)
        else:
            pygame.draw.circle(screen, pygame.Color("red"), (player.x, player.y), 45)

    for post in state.posts:
        pygame.draw.circle(screen, pygame.Color("black"), (post.x, post.y), 15)

    # Atualizar a ecra
    pygame.display.flip()

client_socket.close()
pygame.quit()

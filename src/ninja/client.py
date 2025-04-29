import pygame
import socket
import pickle


# Iniciar pygame
pygame.init()

# Criar socket
client_socket = socket.create_connection(('127.0.0.1', 12345))

# Ler nome
name = input("Nick: ")

# Enviar nome
data = pickle.dumps(name)
data = len(data).to_bytes(4, "big") + data
client_socket.sendall(data)

# Iniciar ecra
screen = pygame.display.set_mode((720, 720))

running = True

# Ciclo do jogo
while running:
    # Boilerplate para eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Iniciar estrutura de input
    move = {"x": 0, "y": 0, "kick": False}

    # Ler input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        move["y"] = -1
    if keys[pygame.K_s]:
        move["y"] = 1
    if keys[pygame.K_a]:
        move["x"] = -1
    if keys[pygame.K_d]:
        move["x"] = 1
    if keys[pygame.K_SPACE]:
        move["kick"] = True

    # Enviar input para o servidor
    data = pickle.dumps(move)
    data = len(data).to_bytes(4, "big") + data
    client_socket.sendall(data)

    # Receber estado atualizado do servidor
    size = int.from_bytes(client_socket.recv(4), "big")
    data = client_socket.recv(size)
    state = pickle.loads(data)

    # Desenhar fundo
    screen.fill("green")

    # Desenhar bola
    pygame.draw.circle(screen, pygame.Color("white"), (state.ball.x, state.ball.y), 30)

    # Desenhar jogadores
    for p in state.players.values():
        pygame.draw.circle(screen, pygame.Color("blue"), (p.x, p.y), 45)

    # Atualizar a ecra
    pygame.display.flip()


client_socket.close()
pygame.quit()

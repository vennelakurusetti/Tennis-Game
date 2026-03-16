import pygame
import sys
import random
import math

pygame.init()
pygame.mixer.quit()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Screen setup
WIDTH, HEIGHT = 1000, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tennis Game")

# Colors & fonts
PINK = (255, 105, 180)
BLUE = (0, 153, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
font_large = pygame.font.SysFont("Segoe UI", 48, bold=True)
font_medium = pygame.font.SysFont("Segoe UI", 32)

# Game objects
player = pygame.Rect(50, HEIGHT // 2, 20, 80)
computer = pygame.Rect(WIDTH - 70, HEIGHT // 2, 20, 80)
ball = pygame.Rect(WIDTH // 2, HEIGHT // 2, 20, 20)

# Game state
ball_speed_x = 7
ball_speed_y = 7
gravity = 0.5
player_score = 0
computer_score = 0
game_over = False
game_started = False
entering_name = True
player_name = ""
show_restart_message = False
winner_text = ""
final_score_text = ""
win_score = 7
display_played = False
paused = False

# Load sounds (.wav recommended)
hit_sound = pygame.mixer.Sound("assets/hit.mp3")
score_sound = pygame.mixer.Sound("assets/score.mp3")
click_sound = pygame.mixer.Sound("assets/click.mp3")
display_sound = pygame.mixer.Sound("assets/display.mp3")

# Set volumes
for sound in [hit_sound, score_sound, click_sound, display_sound]:
    sound.set_volume(20.0)

clock = pygame.time.Clock()

# Button setup
button_width, button_height = 180, 50
button_x = (WIDTH - button_width) // 2
button_y = 260
button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
pause_button_rect = pygame.Rect(WIDTH - 200, 60, 120, 40)

class ConfettiParticle:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = 180
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 7)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2
        self.gravity = 0.1
        self.size = random.randint(4, 8)
        self.life = random.randint(50, 100)
        self.color = random.choice([
            (255, 50, 50), (50, 255, 50), (50, 50, 255),
            (255, 255, 50), (255, 0, 255), (0, 255, 255),
            (255, 165, 0), (138, 43, 226)
        ])
        self.shape = random.choice(["circle", "rect"])
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-5, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        self.rotation += self.rotation_speed

    def draw(self, surface):
        if self.life <= 0:
            return
        if self.shape == "circle":
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
        elif self.shape == "rect":
            rect_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.rect(rect_surf, self.color, (0, 0, self.size, self.size))
            rotated = pygame.transform.rotate(rect_surf, self.rotation)
            rect = rotated.get_rect(center=(self.x, self.y))
            surface.blit(rotated, rect)

confetti_particles = []

def draw_text(text, x, y, color=WHITE, center=False, font=font_large):
    img = font.render(text, True, color)
    rect = img.get_rect()
    rect.center = (x, y) if center else (x, y)
    screen.blit(img, rect)

def draw_button(text="Enter", y_offset=0, rect=None):
    if rect is None:
        rect = button_rect.move(0, y_offset)
    pygame.draw.rect(screen, (0, 0, 0, 100), rect.move(4, 4), border_radius=8)
    pygame.draw.rect(screen, WHITE, rect, border_radius=8)
    draw_text(text, rect.centerx, rect.centery, color=BLACK, center=True, font=font_medium)
    return rect

def draw_gradient_background(color_top, color_bottom):
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

def reset_ball():
    global ball_speed_x, ball_speed_y
    ball.x = WIDTH // 2
    ball.y = random.randint(100, HEIGHT - 100)
    ball_speed_x = random.choice([-7, 7])
    ball_speed_y = random.choice([-7, 7])

reset_ball()

pygame.mixer.music.load("assets/bk.mp3")  # replace with your file
pygame.mixer.music.set_volume(0.3)  # adjust volume (0.0 to 1.0)
pygame.mixer.music.play(-1)

# Game loop
while True:
    draw_gradient_background(PINK, BLUE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if entering_name:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name.strip():
                    entering_name = False
                    game_started = True
                    click_sound.play()
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif len(player_name) < 12:
                    player_name += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
                if player_name.strip():
                    entering_name = False
                    game_started = True
                    click_sound.play()

        elif game_over and show_restart_message:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.collidepoint(event.pos):
                    game_over = False
                    show_restart_message = False
                    reset_ball()
                    player_score = 0
                    computer_score = 0
                    display_played = False
                    confetti_particles.clear()
                    click_sound.play()
                elif exit_button.collidepoint(event.pos):
                    click_sound.play()
                    pygame.quit()
                    sys.exit()

        if game_started and not game_over and event.type == pygame.MOUSEBUTTONDOWN:
            if pause_button_rect.collidepoint(event.pos):
                paused = not paused
                click_sound.play()

        if event.type == pygame.USEREVENT:
            show_restart_message = True
            pygame.time.set_timer(pygame.USEREVENT, 0)

    if entering_name:
        pygame.draw.rect(screen, GRAY, (WIDTH // 2 - 246, 84, 500, 250), border_radius=12)
        pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 250, 80, 500, 250), border_radius=12)
        draw_text("TENNIS GAME", WIDTH // 2, 100, color=BLACK, center=True)
        draw_text("Enter name:", WIDTH // 2, 160, color=BLACK, center=True)
        draw_text(player_name if player_name else "Type here...", WIDTH // 2, 200, color=GRAY, center=True, font=font_medium)
        draw_button()

    elif game_started and not game_over:
        draw_button("Pause" if not paused else "Resume", rect=pause_button_rect)

        if not paused:
            mouse_y = pygame.mouse.get_pos()[1]
            player.y = max(0, min(mouse_y - player.height // 2, HEIGHT - player.height))
            computer.y += (ball.centery - computer.centery) * 0.1

            ball.x += ball_speed_x
            ball.y += ball_speed_y
            ball_speed_y += gravity

            if ball.y <= 0 or ball.y >= HEIGHT - ball.height:
                ball_speed_y *= -1

            if player.colliderect(ball):
                ball.x = player.right
                ball_speed_x *= -1
                ball_speed_y = random.choice([-10, -8, -6, 6, 8, 10])
                hit_sound.play()

            if computer.colliderect(ball):
                ball.x = computer.left - ball.width
                ball_speed_x *= -1
                ball_speed_y = random.choice([-10, -8, -6, 6, 8, 10])

            if ball.x <= 0:
                computer_score += 1
                score_sound.play()
                reset_ball()
            elif ball.x >= WIDTH:
                player_score += 1
                score_sound.play()
                reset_ball()

            if player_score >= win_score or computer_score >= win_score:
                game_over = True
                winner = "Bot" if computer_score > player_score else player_name
                winner_text = f"{winner} Wins!"
                final_score_text = f"Final Score: {player_score}-{computer_score}"
                pygame.time.set_timer(pygame.USEREVENT, 1500)

        pygame.draw.rect(screen, WHITE, player, border_radius=10)
        pygame.draw.rect(screen, WHITE, computer, border_radius=10)
        pygame.draw.ellipse(screen, (240, 240, 240), ball)

        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 255, 255, 60), (0, 0, 40, 40))
        screen.blit(glow, (ball.x - 10, ball.y - 10))

        draw_text(player_name, 80, 20, font=font_medium)
        draw_text("Bot", WIDTH - 80, 20, font=font_medium)

        # Scoreboard
        pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 70, 10, 140, 40), border_radius=12)
        pygame.draw.rect(screen, BLACK, (WIDTH // 2 - 70, 10, 140, 40), 2, border_radius=12)
        draw_text(f"{player_score} - {computer_score}", WIDTH // 2, 30, color=BLACK, center=True, font=font_medium)

    elif game_over:
        pygame.draw.rect(screen, GRAY, (WIDTH // 2 - 246, 134, 500, 200), border_radius=12)
        pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 250, 130, 500, 200), border_radius=12)
        draw_text("Game Over!", WIDTH // 2, 160, color=BLACK, center=True)
        draw_text(winner_text, WIDTH // 2, 210, color=BLACK, center=True)
        draw_text(final_score_text, WIDTH // 2, 250, color=BLACK, center=True)

        if not display_played:
            display_sound.play()
            for _ in range(120):
                confetti_particles.append(ConfettiParticle())
            display_played = True

        for particle in confetti_particles:
            particle.update()
            particle.draw(screen)
        confetti_particles[:] = [p for p in confetti_particles if p.life > 0]

        restart_button = draw_button("Restart", y_offset=80)
        exit_button = draw_button("Exit", y_offset=150)

    pygame.display.update()
    clock.tick(60)

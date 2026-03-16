import pygame
import sys
import os
import random
import math

pygame.init()
pygame.mixer.quit()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# ─────────────────────────────────────────────────────────────────────────────
# SCREEN SETUP
# ─────────────────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tennis Champs")
clock = pygame.time.Clock()

# ─────────────────────────────────────────────────────────────────────────────
# FONTS
# ─────────────────────────────────────────────────────────────────────────────
try:
    font_title  = pygame.font.Font(None, 84)
    font_large  = pygame.font.Font(None, 52)
    font_medium = pygame.font.Font(None, 36)
    font_small  = pygame.font.Font(None, 28)
    font_tiny   = pygame.font.Font(None, 20)
except Exception:
    font_title  = pygame.font.SysFont("Arial", 72, bold=True)
    font_large  = pygame.font.SysFont("Arial", 48, bold=True)
    font_medium = pygame.font.SysFont("Arial", 32)
    font_small  = pygame.font.SysFont("Arial", 24)
    font_tiny   = pygame.font.SysFont("Arial", 18)

# ─────────────────────────────────────────────────────────────────────────────
# COLOURS
# ─────────────────────────────────────────────────────────────────────────────
WHITE           = (255, 255, 255)
BLACK           = (0,   0,   0)
DARK_GRAY       = (30,  30,  35)
GRAY            = (80,  80,  90)
LIGHT_GRAY      = (200, 200, 210)
NEON_BLUE       = (0,   255, 255)
NEON_GREEN      = (57,  255, 20)
NEON_PINK       = (255, 20,  147)
ELECTRIC_PURPLE = (138, 43,  226)
GOLD            = (255, 215, 0)
SILVER          = (192, 192, 192)

GRADIENT_COLORS = {
    'cyberpunk': [(75, 0, 130), (255, 20, 147), (0, 255, 255)],
    'sunset':    [(255, 94, 77), (255, 154, 0), (255, 206, 84)],
    'ocean':     [(0, 119, 190), (0, 180, 216), (144, 224, 239)],
    'forest':    [(76, 175, 80), (139, 195, 74), (205, 220, 57)],
}

# ─────────────────────────────────────────────────────────────────────────────
# SOUND  –  load from assets/ folder, fall back to silence on any error
# ─────────────────────────────────────────────────────────────────────────────
ASSET_DIR = "assets"

def _load(filename):
    """Load a sound file safely; return None if it cannot be loaded."""
    path = os.path.join(ASSET_DIR, filename)
    try:
        snd = pygame.mixer.Sound(path)
        snd.set_volume(0.6)
        return snd
    except Exception as e:
        print(f"[audio] Could not load '{path}': {e}")
        return None

# Match the four sound names from your original code 1
hit_sound     = _load("hit.mp3")      # ball-paddle hit
score_sound   = _load("score.mp3")    # point scored
click_sound   = _load("click.mp3")    # UI button click
display_sound = _load("display.mp3")  # game-over fanfare

def play(snd):
    """Play a Sound object if it loaded successfully."""
    if snd:
        snd.play()

# Background music (looping) – same file as code 1
_bgm_path = os.path.join(ASSET_DIR, "bk.mp3")
if os.path.isfile(_bgm_path):
    try:
        pygame.mixer.music.load(_bgm_path)
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"[audio] BGM failed: {e}")
else:
    print(f"[audio] BGM file not found at '{_bgm_path}', skipping.")

# ─────────────────────────────────────────────────────────────────────────────
# GAME STATE FLAGS
# ─────────────────────────────────────────────────────────────────────────────
show_start_screen  = True
transitioning      = False
show_name_entry    = False
game_started       = False
show_restart_msg   = False
player_name        = ""
current_theme      = "cyberpunk"

winner_text     = ""
final_score_txt = ""
display_played  = False          # victory sound guard (like code 1's display_played)
paused          = False

# Animation
title_y       = HEIGHT // 2 - 80
move_title_to = 50
title_pulse   = 0.0
particle_time = 0.0
fade_surface  = pygame.Surface((WIDTH, HEIGHT))
fade_surface.fill(BLACK)
fade_alpha    = 0

# ─────────────────────────────────────────────────────────────────────────────
# BUTTON CLASS
# ─────────────────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, color,
                 text_color=BLACK, border_radius=15):
        self.rect          = pygame.Rect(x, y, w, h)
        self.text          = text
        self.color         = color
        self.text_color    = text_color
        self.border_radius = border_radius
        self.hover_scale   = 1.0

    def draw(self, surface, font=font_medium):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.hover_scale = min(1.08, self.hover_scale + 0.05)
        else:
            self.hover_scale = max(1.00, self.hover_scale - 0.05)

        sr = self.rect.copy()
        if self.hover_scale > 1.0:
            d = (self.hover_scale - 1.0) * 20
            sr.inflate_ip(d, d)

        # shadow
        shadow = sr.move(4, 4)
        pygame.draw.rect(surface, BLACK, shadow, border_radius=self.border_radius)
        pygame.draw.rect(surface, self.color, sr, border_radius=self.border_radius)
        pygame.draw.rect(surface, WHITE,      sr, 3, border_radius=self.border_radius)

        ts = font.render(self.text, True, self.text_color)
        surface.blit(ts, ts.get_rect(center=sr.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# ─────────────────────────────────────────────────────────────────────────────
# PARTICLES
# ─────────────────────────────────────────────────────────────────────────────
class BackgroundParticle:
    def __init__(self):
        self.x     = random.randint(0, WIDTH)
        self.y     = random.randint(0, HEIGHT)
        self.vx    = random.uniform(-0.8, 0.8)
        self.vy    = random.uniform(-0.8, 0.8)
        self.size  = random.randint(1, 3)
        self.color = random.choice([NEON_BLUE, NEON_GREEN, NEON_PINK, WHITE])

    def update(self):
        self.x = (self.x + self.vx) % WIDTH
        self.y = (self.y + self.vy) % HEIGHT

    def draw(self, surface):
        pygame.draw.circle(surface, self.color,
                           (int(self.x), int(self.y)), self.size)


class ConfettiParticle:
    def __init__(self, x=WIDTH // 2, y=HEIGHT // 2):
        self.x  = x
        self.y  = y
        angle   = random.uniform(0, 2 * math.pi)
        speed   = random.uniform(3, 10)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 3
        self.gravity       = 0.15
        self.size          = random.randint(6, 12)
        self.life          = random.randint(60, 120)
        self.max_life      = self.life
        self.color         = random.choice(
            [NEON_PINK, NEON_BLUE, NEON_GREEN, GOLD, ELECTRIC_PURPLE])
        self.shape         = random.choice(["circle", "rect", "triangle"])
        self.rotation      = random.uniform(0, 360)
        self.rotation_spd  = random.uniform(-8, 8)

    def update(self):
        self.x        += self.vx
        self.y        += self.vy
        self.vy       += self.gravity
        self.vx       *= 0.99
        self.life     -= 1
        self.rotation += self.rotation_spd

    def draw(self, surface):
        if self.life <= 0:
            return
        if self.shape == "circle":
            pygame.draw.circle(surface, self.color,
                               (int(self.x), int(self.y)), self.size)
        elif self.shape == "rect":
            rs = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.rect(rs, (*self.color, 200),
                             (0, 0, self.size, self.size))
            rot = pygame.transform.rotate(rs, self.rotation)
            surface.blit(rot, rot.get_rect(center=(self.x, self.y)))
        elif self.shape == "triangle":
            pts = []
            for i in range(3):
                a = math.radians(self.rotation + i * 120)
                pts.append((self.x + math.cos(a) * self.size,
                             self.y + math.sin(a) * self.size))
            pygame.draw.polygon(surface, self.color, pts)

# ─────────────────────────────────────────────────────────────────────────────
# PADDLE CLASS
# ─────────────────────────────────────────────────────────────────────────────
class Paddle:
    def __init__(self, x, y, width=20, height=80):
        self.rect      = pygame.Rect(x, y, width, height)
        self.trail     = []
        self.glow_size = 0

    def update_trail(self):
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 10:
            self.trail.pop(0)

    def draw(self, surface, color=WHITE):
        # motion trail
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / max(len(self.trail), 1)) * 0.3)
            ts = pygame.Surface(
                (self.rect.width + 4, self.rect.height + 4), pygame.SRCALPHA)
            pygame.draw.rect(ts, (*color, alpha),
                             (0, 0, self.rect.width + 4, self.rect.height + 4),
                             border_radius=15)
            surface.blit(ts, (pos[0] - (self.rect.width + 4) // 2,
                               pos[1] - (self.rect.height + 4) // 2))
        # glow on hit
        if self.glow_size > 0:
            gs = pygame.Surface(
                (self.rect.width  + self.glow_size * 2,
                 self.rect.height + self.glow_size * 2), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*NEON_BLUE, 100),
                             (0, 0,
                              self.rect.width  + self.glow_size * 2,
                              self.rect.height + self.glow_size * 2),
                             border_radius=20)
            surface.blit(gs, (self.rect.x - self.glow_size,
                               self.rect.y - self.glow_size))
            self.glow_size = max(0, self.glow_size - 1)

        pygame.draw.rect(surface, color, self.rect, border_radius=15)
        pygame.draw.rect(surface, NEON_BLUE, self.rect, 3, border_radius=15)

# ─────────────────────────────────────────────────────────────────────────────
# BALL CLASS
# ─────────────────────────────────────────────────────────────────────────────
class Ball:
    def __init__(self, x, y, size=20):
        self.rect           = pygame.Rect(x, y, size, size)
        self.trail          = []
        self.spark_particles = []

    def update_trail(self):
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 15:
            self.trail.pop(0)

    def add_spark(self):
        for _ in range(4):
            self.spark_particles.append({
                'x':    self.rect.centerx + random.randint(-5, 5),
                'y':    self.rect.centery + random.randint(-5, 5),
                'vx':   random.uniform(-3, 3),
                'vy':   random.uniform(-3, 3),
                'life': random.randint(10, 20),
                'size': random.randint(2, 4),
            })

    def update_sparks(self):
        for sp in self.spark_particles[:]:
            sp['x']    += sp['vx']
            sp['y']    += sp['vy']
            sp['life'] -= 1
            if sp['life'] <= 0:
                self.spark_particles.remove(sp)

    def draw(self, surface):
        # trail
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / max(len(self.trail), 1)) * 0.4)
            sz    = max(2, int(self.rect.width * (i / max(len(self.trail), 1))))
            ts    = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(ts, (*NEON_PINK, alpha), (sz, sz), sz)
            surface.blit(ts, (pos[0] - sz, pos[1] - sz))

        # sparks
        for sp in self.spark_particles:
            pygame.draw.circle(
                surface, GOLD,
                (int(sp['x']), int(sp['y'])), sp['size'])

        # glow
        glow = pygame.Surface(
            (self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA)
        pygame.draw.circle(
            glow, (*NEON_PINK, 100),
            (self.rect.width // 2 + 10, self.rect.height // 2 + 10),
            self.rect.width // 2 + 10)
        surface.blit(glow, (self.rect.x - 10, self.rect.y - 10))

        # ball body
        pygame.draw.circle(surface, WHITE, self.rect.center, self.rect.width // 2)
        pygame.draw.circle(surface, NEON_PINK, self.rect.center,
                           self.rect.width // 2, 3)

# ─────────────────────────────────────────────────────────────────────────────
# GAME OBJECTS & PHYSICS STATE
# ─────────────────────────────────────────────────────────────────────────────
player_paddle   = Paddle(50, HEIGHT // 2)
computer_paddle = Paddle(WIDTH - 70, HEIGHT // 2)
ball            = Ball(WIDTH // 2, HEIGHT // 2)

ball_speed_x = 7.0
ball_speed_y = 7.0
GRAVITY      = 0.3          # gentle downward pull each frame

# Score / win condition
player_score   = 0
computer_score = 0
WIN_SCORE      = 7

# Floor / bounce constants
FLOOR_Y          = HEIGHT - ball.rect.height   # y where ball bottom hits floor
CEIL_Y           = 0                            # y where ball top hits ceiling
# If ball bottom is closer than this to the floor the bot will "scoop" it
FLOOR_DANGER_PX  = 90
# Minimum upward speed guaranteed after a floor bounce
MIN_BOUNCE_UP    = 6.0
# Speed cap – prevents ball accelerating forever
MAX_SPEED_Y      = 14.0
MAX_SPEED_X      = 16.0

# Particles / confetti
background_particles = [BackgroundParticle() for _ in range(30)]
confetti_particles   = []

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: GRADIENT BACKGROUND (pre-render once per theme)
# ─────────────────────────────────────────────────────────────────────────────
def make_gradient(colors, w=WIDTH, h=HEIGHT):
    surf = pygame.Surface((w, h))
    n    = len(colors)
    if n < 2:
        surf.fill(colors[0] if colors else BLACK)
        return surf
    for y in range(h):
        p   = y / h
        seg = 1.0 / (n - 1)
        si  = min(int(p / seg), n - 2)
        lp  = (p - si * seg) / seg
        c1, c2 = colors[si], colors[si + 1]
        r = int(c1[0] + (c2[0] - c1[0]) * lp)
        g = int(c1[1] + (c2[1] - c1[1]) * lp)
        b = int(c1[2] + (c2[2] - c1[2]) * lp)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
    return surf

gradient_bg = make_gradient(GRADIENT_COLORS[current_theme])

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: GLOWING TEXT
# ─────────────────────────────────────────────────────────────────────────────
def draw_glow_text(text, x, y, font,
                   color=WHITE, glow_color=NEON_BLUE, center=False):
    ts = font.render(text, True, color)
    gs = font.render(text, True, glow_color)
    if center:
        tr = ts.get_rect(center=(x, y))
        gr = gs.get_rect(center=(x, y))
    else:
        tr = pygame.Rect(x, y, 0, 0)
        gr = pygame.Rect(x, y, 0, 0)
    for ox, oy in [(2,2),(-2,-2),(2,-2),(-2,2),(0,2),(0,-2),(2,0),(-2,0)]:
        screen.blit(gs, gr.move(ox, oy) if center else (gr.x+ox, gr.y+oy))
    screen.blit(ts, tr)

# ─────────────────────────────────────────────────────────────────────────────
# BALL RESET  – always start away from the floor
# ─────────────────────────────────────────────────────────────────────────────
def reset_ball():
    global ball_speed_x, ball_speed_y
    ball.rect.x = WIDTH  // 2
    # Keep reset y well above the floor (top 60 % of the court)
    ball.rect.y = random.randint(60, int(HEIGHT * 0.45))
    ball_speed_x = random.choice([-7.0, 7.0])
    # Always launch slightly upward so gravity has somewhere to act
    ball_speed_y = random.uniform(-8.0, -4.0)
    ball.trail.clear()
    ball.spark_particles.clear()

reset_ball()

# ─────────────────────────────────────────────────────────────────────────────
# GAME-OVER HELPER
# ─────────────────────────────────────────────────────────────────────────────
def handle_game_over():
    global winner_text, final_score_txt, confetti_particles, display_played
    if player_score >= WIN_SCORE:
        winner_text = f"🏆 {player_name} Wins! 🏆"
        n_conf = 120
    else:
        winner_text = "🤖 Bot Wins! 🤖"
        n_conf = 60

    for _ in range(n_conf):
        confetti_particles.append(
            ConfettiParticle(WIDTH // 2, HEIGHT // 3))

    final_score_txt = f"Final Score: {player_score} - {computer_score}"

    if not display_played:
        play(display_sound)          # ← victory fanfare from code 1
        display_played = True

# ─────────────────────────────────────────────────────────────────────────────
# RESTART
# ─────────────────────────────────────────────────────────────────────────────
def restart_game():
    global player_score, computer_score, show_restart_msg
    global game_started, confetti_particles, display_played, paused
    player_score   = 0
    computer_score = 0
    show_restart_msg = False
    game_started   = True
    display_played = False
    paused         = False
    confetti_particles.clear()
    player_paddle.trail.clear()
    computer_paddle.trail.clear()
    reset_ball()

# ─────────────────────────────────────────────────────────────────────────────
# UI BUTTONS  (created once; re-used every frame)
# ─────────────────────────────────────────────────────────────────────────────
start_button      = Button(WIDTH // 2 - 100, HEIGHT - 120, 200, 60,
                           "Start Game", NEON_GREEN)
enter_button      = Button(WIDTH // 2 - 60, HEIGHT // 2 + 60, 120, 40,
                           "Enter", NEON_BLUE)
pause_btn_rect    = pygame.Rect(WIDTH - 160, 10, 110, 36)   # pause/resume

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────
running = True
while running:
    dt            = clock.tick(60) / 1000.0
    particle_time += dt
    title_pulse   += dt * 3

    # ── EVENT HANDLING ────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ── START SCREEN ──────────────────────────────────────────────────────
        if show_start_screen:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.is_clicked(event.pos):
                    transitioning = True
                    play(click_sound)

        # ── NAME ENTRY ────────────────────────────────────────────────────────
        elif show_name_entry:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name.strip():
                    show_name_entry = False
                    game_started    = True
                    play(click_sound)
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif len(player_name) < 15 and event.unicode.isprintable():
                    player_name += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if enter_button.is_clicked(event.pos) and player_name.strip():
                    show_name_entry = False
                    game_started    = True
                    play(click_sound)

        # ── GAMEPLAY ──────────────────────────────────────────────────────────
        elif game_started:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_started      = False
                    show_start_screen = True
                    play(click_sound)
                elif event.key == pygame.K_p:
                    paused = not paused
                    play(click_sound)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if pause_btn_rect.collidepoint(event.pos):
                    paused = not paused
                    play(click_sound)

        # ── RESTART / GAME-OVER SCREEN ────────────────────────────────────────
        elif show_restart_msg:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    restart_game()
                    play(click_sound)
                elif event.key == pygame.K_ESCAPE:
                    show_restart_msg  = False
                    show_start_screen = True
                    confetti_particles.clear()
                    play(click_sound)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                play_btn_r = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 + 50,
                                         180, 50)
                menu_btn_r = pygame.Rect(WIDTH // 2 + 20,  HEIGHT // 2 + 50,
                                         180, 50)
                if play_btn_r.collidepoint(event.pos):
                    restart_game()
                    play(click_sound)
                elif menu_btn_r.collidepoint(event.pos):
                    show_restart_msg  = False
                    show_start_screen = True
                    confetti_particles.clear()
                    play(click_sound)

    # ── UPDATE BACKGROUND PARTICLES ───────────────────────────────────────────
    for bp in background_particles:
        bp.update()

    # ─────────────────────────────────────────────────────────────────────────
    # RENDER
    # ─────────────────────────────────────────────────────────────────────────
    screen.fill(BLACK)

    # ══════════════════════════════════════════════════════════════════════════
    # START SCREEN
    # ══════════════════════════════════════════════════════════════════════════
    if show_start_screen:
        screen.blit(gradient_bg, (0, 0))
        for bp in background_particles:
            bp.draw(screen)

        draw_glow_text("TENNIS CHAMPS", WIDTH // 2, title_y,
                       font_title, WHITE, NEON_BLUE, center=True)
        draw_glow_text("Ultimate Championship Edition",
                       WIDTH // 2, title_y + 80,
                       font_medium, LIGHT_GRAY, NEON_PINK, center=True)
        start_button.draw(screen, font_large)

        v = font_tiny.render("v2.1 – Enhanced + Sound", True, GRAY)
        screen.blit(v, (10, HEIGHT - 25))

        if transitioning:
            title_y   += (move_title_to - title_y) * 0.15
            fade_alpha += 8
            if fade_alpha >= 255:
                fade_alpha        = 0
                transitioning     = False
                show_start_screen = False
                show_name_entry   = True
                title_y           = HEIGHT // 2 - 80
            fade_surface.set_alpha(fade_alpha)
            screen.blit(fade_surface, (0, 0))

    # ══════════════════════════════════════════════════════════════════════════
    # NAME ENTRY
    # ══════════════════════════════════════════════════════════════════════════
    elif show_name_entry:
        screen.blit(gradient_bg, (0, 0))
        for bp in background_particles:
            bp.draw(screen)

        dlg = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 - 150, 600, 300)
        pygame.draw.rect(screen, BLACK,
                         dlg.move(8, 8), border_radius=25)
        ds = pygame.Surface((dlg.width, dlg.height), pygame.SRCALPHA)
        pygame.draw.rect(ds, (30, 30, 40, 240),
                         (0, 0, dlg.width, dlg.height), border_radius=25)
        screen.blit(ds, dlg)
        pygame.draw.rect(screen, NEON_BLUE, dlg, 3, border_radius=25)

        draw_glow_text("TENNIS CHAMPS",
                       WIDTH // 2, HEIGHT // 2 - 100,
                       font_large, WHITE, NEON_BLUE, center=True)
        draw_glow_text("Enter Player Name",
                       WIDTH // 2, HEIGHT // 2 - 50,
                       font_medium, LIGHT_GRAY, NEON_PINK, center=True)

        ir = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 10, 400, 50)
        pygame.draw.rect(screen, DARK_GRAY, ir, border_radius=15)
        pygame.draw.rect(screen, NEON_BLUE if player_name else GRAY,
                         ir, 2, border_radius=15)

        disp = player_name if player_name else "Enter your champion name..."
        ns   = font_medium.render(disp, True, WHITE if player_name else GRAY)
        nsr  = ns.get_rect(center=ir.center)
        screen.blit(ns, nsr)

        # blinking cursor
        if player_name and int(particle_time * 2) % 2:
            cx = nsr.right + 5
            pygame.draw.line(screen, WHITE,
                             (cx, ir.y + 10), (cx, ir.bottom - 10), 2)

        enter_button.color      = NEON_GREEN if player_name.strip() else GRAY
        enter_button.text_color = BLACK      if player_name.strip() else DARK_GRAY
        enter_button.rect.center = (WIDTH // 2, HEIGHT // 2 + 70)
        enter_button.draw(screen, font_medium)

        hi = font_small.render("Press ENTER to continue", True, LIGHT_GRAY)
        screen.blit(hi, hi.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120)))

    # ══════════════════════════════════════════════════════════════════════════
    # GAMEPLAY
    # ══════════════════════════════════════════════════════════════════════════
    elif game_started:
        screen.blit(gradient_bg, (0, 0))
        for bp in background_particles:
            bp.draw(screen)

        # ── PAUSE BUTTON ──────────────────────────────────────────────────────
        lbl = "Resume" if paused else "Pause"
        pygame.draw.rect(screen, DARK_GRAY, pause_btn_rect, border_radius=8)
        pygame.draw.rect(screen, NEON_BLUE, pause_btn_rect, 2, border_radius=8)
        ps = font_tiny.render(lbl, True, WHITE)
        screen.blit(ps, ps.get_rect(center=pause_btn_rect.center))

        if not paused:
            # ── PLAYER PADDLE (mouse) ─────────────────────────────────────────
            my = pygame.mouse.get_pos()[1]
            ty = max(0, min(my - player_paddle.rect.height // 2,
                            HEIGHT - player_paddle.rect.height))
            player_paddle.rect.y += (ty - player_paddle.rect.y) * 0.18
            player_paddle.update_trail()

            # ── COMPUTER AI ───────────────────────────────────────────────────
            # Predict where ball will land on the computer's x-column
            if ball_speed_x > 0:
                frames_away = (computer_paddle.rect.x - ball.rect.x) / ball_speed_x
                pred_y = (ball.rect.y
                          + ball_speed_y * frames_away
                          + 0.5 * GRAVITY * frames_away ** 2)
            else:
                pred_y = ball.rect.centery

            # Default: centre paddle on predicted ball position
            ai_target_y = pred_y - computer_paddle.rect.height // 2

            # ── FLOOR SCOOP LOGIC ─────────────────────────────────────────────
            # If ball is dangerously low the bot aims to hit with its UPPER edge,
            # which deflects the ball upward.  We also ensure the ball itself
            # gets an upward nudge if it has nearly stopped vertically.
            ball_is_low = ball.rect.bottom >= HEIGHT - FLOOR_DANGER_PX

            if ball_is_low:
                # Aim so the top quarter of the paddle meets the ball
                ai_target_y = ball.rect.centery - computer_paddle.rect.height * 0.80
                # If ball is almost resting on the floor give it an upward kick
                if ball.rect.bottom >= FLOOR_Y - 4 and ball_speed_y >= 0:
                    ball.rect.bottom = FLOOR_Y - 2
                    ball_speed_y = -max(abs(ball_speed_y) * 0.85, MIN_BOUNCE_UP)
                    ball.add_spark()

            computer_paddle.rect.y += (ai_target_y - computer_paddle.rect.y) * 0.09
            computer_paddle.rect.y  = max(
                0, min(computer_paddle.rect.y, HEIGHT - computer_paddle.rect.height))
            computer_paddle.update_trail()

            # ── BALL PHYSICS ──────────────────────────────────────────────────
            ball.rect.x  += int(ball_speed_x)
            ball.rect.y  += int(ball_speed_y)
            ball_speed_y  = min(ball_speed_y + GRAVITY, MAX_SPEED_Y)
            ball_speed_x  = max(-MAX_SPEED_X, min(ball_speed_x, MAX_SPEED_X))
            ball.update_trail()
            ball.update_sparks()

            # Ceiling bounce
            if ball.rect.top <= CEIL_Y:
                ball.rect.top = CEIL_Y + 1
                ball_speed_y  = abs(ball_speed_y) * 0.9
                ball.add_spark()

            # Floor bounce – guarantee enough upward speed so ball never slides
            if ball.rect.bottom >= FLOOR_Y:
                ball.rect.bottom = FLOOR_Y - 1
                bounced = -abs(ball_speed_y) * 0.85
                # Enforce minimum upward bounce
                ball_speed_y = min(bounced, -MIN_BOUNCE_UP)
                ball.add_spark()

            # ── PADDLE COLLISIONS ─────────────────────────────────────────────
            # Player paddle
            if (player_paddle.rect.colliderect(ball.rect)
                    and ball_speed_x < 0):
                ball.rect.left  = player_paddle.rect.right + 1
                ball_speed_x    = abs(ball_speed_x) * 1.04
                hit_pos         = ((ball.rect.centery - player_paddle.rect.centery)
                                   / player_paddle.rect.height)
                ball_speed_y    = hit_pos * 12 + random.uniform(-2, 2)
                # If ball is low, slant it upward
                if ball.rect.centery > HEIGHT * 0.65 and ball_speed_y > 0:
                    ball_speed_y = -abs(ball_speed_y)
                player_paddle.glow_size = 15
                ball.add_spark()
                play(hit_sound)         # ← sound from code 1

            # Computer paddle
            if (computer_paddle.rect.colliderect(ball.rect)
                    and ball_speed_x > 0):
                ball.rect.right  = computer_paddle.rect.left - 1
                ball_speed_x     = -abs(ball_speed_x) * 1.04
                hit_pos          = ((ball.rect.centery - computer_paddle.rect.centery)
                                    / computer_paddle.rect.height)
                ball_speed_y     = hit_pos * 12 + random.uniform(-2, 2)
                # Bot always scoops low balls upward
                if ball_is_low and ball_speed_y > -3:
                    ball_speed_y = -(abs(ball_speed_y) + 5)
                computer_paddle.glow_size = 15
                ball.add_spark()
                play(hit_sound)         # ← sound from code 1

            # ── SCORING ───────────────────────────────────────────────────────
            if ball.rect.left <= 0:
                computer_score += 1
                play(score_sound)       # ← sound from code 1
                reset_ball()
                for _ in range(20):
                    confetti_particles.append(
                        ConfettiParticle(WIDTH - 100, HEIGHT // 2))

            elif ball.rect.right >= WIDTH:
                player_score += 1
                play(score_sound)       # ← sound from code 1
                reset_ball()
                for _ in range(20):
                    confetti_particles.append(
                        ConfettiParticle(100, HEIGHT // 2))

            # ── GAME-OVER CHECK ───────────────────────────────────────────────
            if player_score >= WIN_SCORE or computer_score >= WIN_SCORE:
                game_started     = False
                show_restart_msg = True
                handle_game_over()   # plays display_sound from code 1

        # ── DRAW COURT ────────────────────────────────────────────────────────
        # Dashed centre line
        for i in range(15):
            if i % 2 == 0:
                yp = i * (HEIGHT // 15)
                pygame.draw.rect(
                    screen, (*NEON_BLUE, 150),
                    (WIDTH // 2 - 3, yp, 6, HEIGHT // 30),
                    border_radius=3)

        # Danger-zone floor tint (subtle red glow near floor)
        floor_surf = pygame.Surface((WIDTH, FLOOR_DANGER_PX), pygame.SRCALPHA)
        floor_surf.fill((255, 0, 0, 18))
        screen.blit(floor_surf, (0, HEIGHT - FLOOR_DANGER_PX))

        player_paddle.draw(screen, NEON_GREEN)
        computer_paddle.draw(screen, NEON_PINK)
        ball.draw(screen)

        # Confetti mini bursts
        for p in confetti_particles[:]:
            p.update()
            p.draw(screen)
        confetti_particles[:] = [p for p in confetti_particles if p.life > 0]

        # ── HUD ───────────────────────────────────────────────────────────────
        draw_glow_text(player_name, 80, 15,
                       font_small, NEON_GREEN, NEON_BLUE)
        draw_glow_text("AI CHAMPION", WIDTH - 170, 15,
                       font_small, NEON_PINK, NEON_BLUE)

        # Score box
        sb = pygame.Rect(WIDTH // 2 - 100, 10, 200, 60)
        pygame.draw.rect(screen, (20, 20, 30), sb, border_radius=15)
        pygame.draw.rect(screen, NEON_BLUE, sb, 3, border_radius=15)

        pc = NEON_GREEN if player_score   > computer_score else WHITE
        cc = NEON_PINK  if computer_score > player_score   else WHITE
        screen.blit(font_large.render(str(player_score),   True, pc), (WIDTH//2-55, 20))
        screen.blit(font_large.render("-",                 True, WHITE),(WIDTH//2-12, 20))
        screen.blit(font_large.render(str(computer_score), True, cc), (WIDTH//2+25, 20))

        # Progress bars
        bar_w = 140
        bar_y = 82
        for side, score, bar_color in [
            ("left",  player_score,   NEON_GREEN),
            ("right", computer_score, NEON_PINK),
        ]:
            bx = WIDTH // 2 - bar_w - 15 if side == "left" else WIDTH // 2 + 15
            bg = pygame.Rect(bx, bar_y, bar_w, 8)
            pygame.draw.rect(screen, DARK_GRAY, bg, border_radius=4)
            if score > 0:
                fw = int(bar_w * score / WIN_SCORE)
                pygame.draw.rect(screen, bar_color,
                                 pygame.Rect(bx, bar_y, fw, 8), border_radius=4)

        hint = font_tiny.render(
            "Mouse: move paddle  •  P / button: pause  •  ESC: quit", True, GRAY)
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 12)))

    # ══════════════════════════════════════════════════════════════════════════
    # GAME-OVER / RESTART SCREEN
    # ══════════════════════════════════════════════════════════════════════════
    elif show_restart_msg:
        screen.blit(gradient_bg, (0, 0))
        for bp in background_particles:
            bp.draw(screen)

        # confetti
        for p in confetti_particles[:]:
            p.update()
            if p.life <= 0:
                confetti_particles.remove(p)
            else:
                p.draw(screen)

        # keep a trickle of new confetti for winner
        if player_score >= WIN_SCORE and len(confetti_particles) < 50:
            if random.random() < 0.3:
                confetti_particles.append(
                    ConfettiParticle(random.randint(100, WIDTH - 100),
                                     random.randint(100, HEIGHT - 100)))

        # dialog
        dlg = pygame.Rect(WIDTH // 2 - 350, HEIGHT // 2 - 200, 700, 400)
        pygame.draw.rect(screen, BLACK, dlg.move(10, 10), border_radius=30)
        ds = pygame.Surface((dlg.width, dlg.height), pygame.SRCALPHA)
        pygame.draw.rect(ds, (20, 20, 30, 240),
                         (0, 0, dlg.width, dlg.height), border_radius=30)
        screen.blit(ds, dlg)
        border_col = GOLD if player_score >= WIN_SCORE else NEON_PINK
        pygame.draw.rect(screen, border_col, dlg, 4, border_radius=30)

        wc = GOLD     if player_score >= WIN_SCORE else NEON_PINK
        gc = NEON_GREEN if player_score >= WIN_SCORE else NEON_BLUE
        draw_glow_text(winner_text,
                       WIDTH // 2, HEIGHT // 2 - 120,
                       font_title, wc, gc, center=True)
        draw_glow_text(final_score_txt,
                       WIDTH // 2, HEIGHT // 2 - 60,
                       font_large, WHITE, NEON_BLUE, center=True)

        total = player_score + computer_score
        if total > 0:
            pct = int(player_score / total * 100)
            draw_glow_text(f"Win Rate: {pct}%",
                           WIDTH // 2, HEIGHT // 2 - 10,
                           font_medium, LIGHT_GRAY, NEON_PINK, center=True)

        # buttons
        pa_btn = Button(WIDTH // 2 - 200, HEIGHT // 2 + 50,
                        180, 50, "Play Again", NEON_GREEN)
        mm_btn = Button(WIDTH // 2 + 20,  HEIGHT // 2 + 50,
                        180, 50, "Main Menu", NEON_BLUE)
        pa_btn.draw(screen, font_medium)
        mm_btn.draw(screen, font_medium)

        for i, line in enumerate(["SPACE – Play Again", "ESC – Main Menu"]):
            ls = font_small.render(line, True, LIGHT_GRAY)
            screen.blit(ls, ls.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 130 + i * 25)))

    pygame.display.flip()

pygame.quit()
sys.exit()
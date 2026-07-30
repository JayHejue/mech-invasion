import pygame
import math
import random
import sys

pygame.init()

W, H = 960, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("太空射击")
clock = pygame.time.Clock()
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 32)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (200, 50, 255)
LIGHT_RED = (255, 100, 100, 100)

player = None
enemies = []
bullets = []
grenades = []
boss_bullets = []
warnings = []
explosions = []
particles = []
score = 0
state = "playing"
last_grenade_time = 0
last_laser_time = 0
last_ultimate_time = 0
enemies_killed = 0
boss_spawned = False
boss = None
ultimate_available = False
game_over_done = False
win_show_time = 0
stars = []

for _ in range(100):
    stars.append([random.randint(0, W), random.randint(0, H), random.random() * 2 + 0.5])


class Player:
    def __init__(self):
        self.w = 50
        self.h = 50
        self.x = W // 2 - self.w // 2
        self.y = H - 80
        self.speed = 6
        self.hp = 1

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def draw(self):
        cx, cy = self.x + self.w // 2, self.y + self.h // 2
        # ship body
        pygame.draw.polygon(screen, BLUE, [
            (cx, cy - 25),
            (cx - 20, cy + 15),
            (cx - 8, cy + 5),
            (cx - 8, cy + 20),
            (cx, cy + 25),
            (cx + 8, cy + 20),
            (cx + 8, cy + 5),
            (cx + 20, cy + 15),
        ])

    def move(self, dx, dy):
        self.x = max(0, min(W - self.w, self.x + dx))
        self.y = max(0, min(H - self.h, self.y + dy))


class Enemy:
    def __init__(self):
        self.w = 40
        self.h = 40
        self.x = random.randint(0, W - self.w)
        self.y = -self.h
        self.hp = 30
        self.max_hp = 30
        self.speed = random.uniform(0.8, 1.5)

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self):
        self.y += self.speed

    def draw(self):
        cx, cy = self.x + self.w // 2, self.y + self.h // 2
        # alien ship
        pygame.draw.ellipse(screen, RED, (self.x, self.y, self.w, self.h))
        pygame.draw.circle(screen, YELLOW, (cx - 8, cy - 5), 4)
        pygame.draw.circle(screen, YELLOW, (cx + 8, cy - 5), 4)
        # hp bar
        bar_w = self.w
        ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, RED, (self.x, self.y - 8, bar_w, 4))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 8, bar_w * ratio, 4))

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            return True
        return False


class BossMech:
    def __init__(self):
        self.w = 120
        self.h = 140
        self.x = W // 2 - self.w // 2
        self.y = -self.h
        self.target_y = 50
        self.hp = 1200
        self.max_hp = 1200
        self.speed = 1
        self.shoot_timer = 0
        self.shoot_interval = 300
        self.warning_active = False
        self.warning_x = 0
        self.warning_countdown = 0

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self):
        if self.y < self.target_y:
            self.y += self.speed
            return
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval - 60 and not self.warning_active:
            self.warning_active = True
            self.warning_x = random.randint(0, W - W // 6)
            self.warning_countdown = 60

        if self.warning_active:
            self.warning_countdown -= 1
            if self.warning_countdown <= 0:
                self.warning_active = False
                boss_bullets.append(BossBullet(self.warning_x, self.y + self.h))
                self.shoot_timer = 0

    def draw(self):
        cx, cy = self.x + self.w // 2, self.y + self.h // 2
        # mech body
        pygame.draw.rect(screen, (100, 100, 100), (self.x + 10, self.y + 30, self.w - 20, 70))
        # head
        pygame.draw.rect(screen, (150, 150, 150), (self.x + 30, self.y, self.w - 60, 40))
        # eyes
        pygame.draw.circle(screen, RED, (cx - 20, cy - 50), 8)
        pygame.draw.circle(screen, RED, (cx + 20, cy - 50), 8)
        # arms
        pygame.draw.rect(screen, (120, 120, 120), (self.x, self.y + 40, 15, 50))
        pygame.draw.rect(screen, (120, 120, 120), (self.x + self.w - 15, self.y + 40, 15, 50))
        # legs
        pygame.draw.rect(screen, (120, 120, 120), (self.x + 15, self.y + 100, 25, 40))
        pygame.draw.rect(screen, (120, 120, 120), (self.x + self.w - 40, self.y + 100, 25, 40))
        # cannon on right arm
        pygame.draw.rect(screen, RED, (self.x + self.w - 5, self.y + 50, 10, 30))
        # hp bar
        bar_w = self.w + 40
        bar_x = self.x - 20
        bar_y = self.y - 20
        ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_w, 8))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_w * ratio, 8))
        hp_text = font_small.render(f"BOSS HP: {self.hp}/{self.max_hp}", True, WHITE)
        screen.blit(hp_text, (W // 2 - hp_text.get_width() // 2, bar_y - 25))

        if self.warning_active:
            s = pygame.Surface((W // 6, H), pygame.SRCALPHA)
            s.fill((255, 100, 100, 60))
            screen.blit(s, (self.warning_x, 0))

    def take_damage(self, dmg):
        self.hp -= dmg
        return self.hp <= 0


class BossBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = W // 6
        self.h = H
        self.speed = 8

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self):
        self.y += self.speed

    def draw(self):
        s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        s.fill((255, 0, 0, 80))
        screen.blit(s, (self.x, self.y))


class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 4
        self.h = 16
        self.speed = 12

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self):
        self.y -= self.speed

    def draw(self):
        pygame.draw.rect(screen, GREEN, (self.x, self.y, self.w, self.h))


class Grenade:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.r = 6
        self.speed = 8
        self.active = True
        self.exploded = False
        self.explode_radius = 120
        self.damage = 50

    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r * 2, self.r * 2)

    def update(self):
        self.y -= self.speed
        if self.y < -20:
            self.active = False

    def draw(self):
        if not self.exploded:
            pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), self.r)
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.r // 2)

    def explode(self):
        self.exploded = True
        self.active = False
        for e in enemies:
            dx = e.x + e.w // 2 - self.x
            dy = e.y + e.h // 2 - self.y
            dist = math.hypot(dx, dy)
            if dist < self.explode_radius:
                e.take_damage(self.damage)
        if boss:
            dx = boss.x + boss.w // 2 - self.x
            dy = boss.y + boss.h // 2 - self.y
            dist = math.hypot(dx, dy)
            if dist < self.explode_radius:
                boss.take_damage(self.damage)
        for i in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            particles.append(Particle(self.x, self.y, math.cos(angle) * speed, math.sin(angle) * speed, ORANGE, 30))


class Explosion:
    def __init__(self, x, y, size=1.0):
        self.x = x
        self.y = y
        self.size = size
        self.frame = 0
        self.max_frames = 20
        self.active = True

    def update(self):
        self.frame += 1
        if self.frame >= self.max_frames:
            self.active = False

    def draw(self):
        progress = self.frame / self.max_frames
        radius = int(30 * self.size * progress)
        alpha = int(255 * (1 - progress))
        if radius > 0 and alpha > 0:
            for i in range(3):
                r = int(radius * (1 - i * 0.2))
                if r > 0:
                    color = [ORANGE, RED, YELLOW][i]
                    s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*color, alpha), (r, r), r)
                    screen.blit(s, (self.x - r, self.y - r))


class Particle:
    def __init__(self, x, y, vx, vy, color, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1
        if self.life <= 0:
            self.active = False

    def draw(self):
        alpha = int(255 * (self.life / self.max_life))
        r = max(1, int(3 * (self.life / self.max_life)))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        screen.blit(s, (int(self.x - r), int(self.y - r)))


def reset_game():
    global player, enemies, bullets, grenades, boss_bullets, warnings
    global explosions, particles, score, state, last_grenade_time, last_laser_time
    global last_ultimate_time, enemies_killed, boss_spawned, boss, ultimate_available
    global game_over_done, win_show_time
    player = Player()
    enemies = []
    bullets = []
    grenades = []
    boss_bullets = []
    warnings = []
    explosions = []
    particles = []
    score = 0
    state = "playing"
    last_grenade_time = -5000
    last_laser_time = -500
    last_ultimate_time = -30000
    enemies_killed = 0
    boss_spawned = False
    boss = None
    ultimate_available = False
    game_over_done = False
    win_show_time = 0


def spawn_enemy():
    if not boss_spawned and random.random() < 0.02:
        enemies.append(Enemy())


def check_collisions():
    global enemies_killed, boss_spawned, boss, score, state, ultimate_available, last_ultimate_time

    # bullets vs enemies
    for b in bullets[:]:
        br = b.rect()
        for e in enemies[:]:
            if br.colliderect(e.rect()):
                if e.take_damage(20):
                    enemies_killed += 1
                    score += 10
                    explosions.append(Explosion(e.x + e.w // 2, e.y + e.h // 2, 0.8))
                    enemies.remove(e)
                if b in bullets:
                    bullets.remove(b)
                break

    # bullets vs boss
    if boss:
        for b in bullets[:]:
            if b.rect().colliderect(boss.rect()):
                if boss.take_damage(20):
                    explosions.append(Explosion(boss.x + boss.w // 2, boss.y + boss.h // 2, 3))
                    state = "win"
                    win_show_time = pygame.time.get_ticks()
                if b in bullets:
                    bullets.remove(b)

    # grenades vs enemies
    for g in grenades[:]:
        if not g.exploded:
            gr = g.rect()
            hit = False
            for e in enemies[:]:
                if gr.colliderect(e.rect()):
                    hit = True
                    break
            if boss and gr.colliderect(boss.rect()):
                hit = True
            if hit or g.y < 0:
                g.explode()
                grenades.remove(g)

    # enemies reach bottom
    for e in enemies[:]:
        if e.y + e.h >= H:
            state = "gameover"
            enemies.clear()

    # boss bullet hits player
    if player and boss:
        for bb in boss_bullets[:]:
            if bb.rect().colliderect(player.rect()):
                state = "gameover"
                boss_bullets.clear()

    # boss reaches bottom
    if boss and boss.y + boss.h >= H:
        state = "gameover"

    # check boss spawn
    if enemies_killed >= 50 and not boss_spawned:
        boss_spawned = True
        boss = BossMech()
        enemies.clear()
        ultimate_available = False

    # ultimate available when boss hp <= 600 and cooldown ready
    if boss and boss.hp <= 600:
        now = pygame.time.get_ticks()
        if now - last_ultimate_time >= 30000:
            ultimate_available = True


def fire_laser():
    global last_laser_time
    now = pygame.time.get_ticks()
    if now - last_laser_time >= 500:
        last_laser_time = now
        if player:
            bullets.append(Bullet(player.x + player.w // 2 - 2, player.y - 10))


def fire_grenade():
    global last_grenade_time
    now = pygame.time.get_ticks()
    if now - last_grenade_time >= 5000:
        last_grenade_time = now
        if player:
            grenades.append(Grenade(player.x + player.w // 2, player.y - 10))


def fire_ultimate():
    global last_ultimate_time, ultimate_available, boss
    now = pygame.time.get_ticks()
    if now - last_ultimate_time >= 30000 and ultimate_available and boss:
        last_ultimate_time = now
        boss.take_damage(600)
        ultimate_available = False
        # big explosion
        for _ in range(50):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 12)
            particles.append(Particle(
                boss.x + boss.w // 2, boss.y + boss.h // 2,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.choice([RED, ORANGE, YELLOW, WHITE]), 40
            ))
        explosions.append(Explosion(boss.x + boss.w // 2, boss.y + boss.h // 2, 4))


def draw_ui():
    # laser CD indicator
    now = pygame.time.get_ticks()
    laser_ready = now - last_laser_time >= 500
    grenade_ready = now - last_grenade_time >= 5000
    ult_ready = now - last_ultimate_time >= 30000

    # cooldown bars
    def draw_cd_bar(x, y, ready, cd_left, total_cd, label, color):
        pygame.draw.rect(screen, (60, 60, 60), (x, y, 120, 16))
        if ready:
            pygame.draw.rect(screen, color, (x, y, 120, 16))
        else:
            ratio = 1 - cd_left / total_cd
            pygame.draw.rect(screen, color, (x, y, 120 * ratio, 16))
        lbl = font_small.render(label, True, WHITE)
        screen.blit(lbl, (x, y - 20))

    draw_cd_bar(10, H - 80, laser_ready, 0, 500, "激光枪", GREEN)
    draw_cd_bar(10, H - 50, grenade_ready, now - last_grenade_time, 5000, "榴弹炮", ORANGE)
    draw_cd_bar(10, H - 20, ult_ready and ultimate_available, now - last_ultimate_time, 30000, "终极武器", PURPLE)

    # score and kill count
    score_text = font_small.render(f"得分: {score}  击杀: {enemies_killed}/50", True, WHITE)
    screen.blit(score_text, (W - 200, 20))

    # ultimate prompt
    if ultimate_available and boss:
        prompt = font_medium.render("按 ENTER 启动终极武器!", True, YELLOW)
        screen.blit(prompt, (W // 2 - prompt.get_width() // 2, H // 2 - 100))

    # boss hp
    if boss:
        boss_hp_text = font_small.render(f"BOSS HP: {boss.hp}/{boss.max_hp}", True, RED)
        screen.blit(boss_hp_text, (W // 2 - boss_hp_text.get_width() // 2, 10))


def draw_stars():
    for s in stars:
        s[1] += s[2] * 0.5
        if s[1] > H:
            s[1] = 0
            s[0] = random.randint(0, W)
        pygame.draw.circle(screen, WHITE, (int(s[0]), int(s[1])), max(1, int(s[2])))


def draw_game_over():
    screen.fill(BLACK)
    text = font_large.render("GAME OVER", True, RED)
    screen.blit(text, (W // 2 - text.get_width() // 2, H // 2 - 40))
    text2 = font_medium.render("按 R 重新开始", True, WHITE)
    screen.blit(text2, (W // 2 - text2.get_width() // 2, H // 2 + 30))


def draw_win():
    global game_over_done
    screen.fill(BLACK)

    # explosion particles
    if not game_over_done:
        for _ in range(5):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(5, 20)
            x = random.randint(0, W)
            y = random.randint(0, H)
            particles.append(Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                                      random.choice([RED, ORANGE, YELLOW, WHITE, BLUE, GREEN]), 60))
        game_over_done = True

    for p in particles[:]:
        p.update()
        p.draw()
        if not p.active:
            particles.remove(p)

    text = font_large.render("CONGRATULATION!", True, YELLOW)
    screen.blit(text, (W // 2 - text.get_width() // 2, H // 2 - 60))
    text2 = font_medium.render("You protect the earth!", True, WHITE)
    screen.blit(text2, (W // 2 - text2.get_width() // 2, H // 2 + 20))
    text3 = font_small.render("按 R 重新开始", True, GREEN)
    screen.blit(text3, (W // 2 - text3.get_width() // 2, H // 2 + 80))


def main():
    reset_game()
    running = True
    global state

    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and state in ("gameover", "win"):
                    reset_game()
                if event.key == pygame.K_RETURN and state == "playing":
                    fire_ultimate()
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()

        if state == "playing" and player:
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            if dx or dy:
                mag = math.hypot(dx, dy)
                dx, dy = dx / mag, dy / mag
                player.move(dx * player.speed, dy * player.speed)

            if keys[pygame.K_SPACE]:
                fire_laser()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                fire_grenade()

            spawn_enemy()
            for e in enemies[:]:
                e.update()
                if e.y > H:
                    enemies.remove(e)

            for b in bullets[:]:
                b.update()
                if b.y < -20:
                    bullets.remove(b)

            for g in grenades[:]:
                g.update()
                if not g.active:
                    if g in grenades:
                        grenades.remove(g)

            if boss:
                boss.update()

            for bb in boss_bullets[:]:
                bb.update()
                if bb.y > H:
                    boss_bullets.remove(bb)

            check_collisions()

            for e in explosions[:]:
                e.update()
                if not e.active:
                    explosions.remove(e)

            for p in particles[:]:
                p.update()
                if not p.active:
                    particles.remove(p)

        elif state == "win":
            for p in particles[:]:
                p.update()
                if not p.active:
                    particles.remove(p)

        # draw
        screen.fill(BLACK)
        draw_stars()

        if state == "playing":
            if player:
                player.draw()
            for e in enemies:
                e.draw()
            for b in bullets:
                b.draw()
            for g in grenades:
                g.draw()
            if boss:
                boss.draw()
            for bb in boss_bullets:
                bb.draw()
            for ex in explosions:
                ex.draw()
            for p in particles:
                p.draw()
            draw_ui()
        elif state == "gameover":
            draw_game_over()
        elif state == "win":
            draw_win()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

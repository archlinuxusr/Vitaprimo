import pygame
import random
import math

pygame.init()
pygame.mixer.init()

WINDOW_SIZE = (1080, 720)
FRAME_RATE = 60
COUNTDOWN_MS = 3000

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

shoot_sound = pygame.mixer.Sound("shoot.flac")


def load_images():
    player = pygame.image.load("player.png").convert_alpha()
    player = pygame.transform.scale(player, (15, 15))
    red = pygame.image.load("red_target.png").convert_alpha()
    red = pygame.transform.scale(red, (20, 20))
    green = pygame.image.load("green_target.png").convert_alpha()
    green = pygame.transform.scale(green, (20, 20))
    gun = pygame.image.load("gun.png").convert_alpha()
    gun = pygame.transform.scale(gun, (20, 8))
    return player, red, green, gun


MAPS = [
    [
        pygame.Rect(300, 150, 100, 400),
        pygame.Rect(600, 100, 50, 300),
        pygame.Rect(150, 500, 400, 50),
        pygame.Rect(800, 300, 200, 50),
        pygame.Rect(500, 600, 300, 30),
    ],
    [
        pygame.Rect(300, 100, 480, 30),
        pygame.Rect(300, 550, 480, 30),
        pygame.Rect(300, 100, 30, 200),
        pygame.Rect(750, 380, 30, 200),
        pygame.Rect(450, 320, 180, 30),
    ],
    [
        pygame.Rect(150, 150, 200, 30),
        pygame.Rect(750, 150, 200, 30),
        pygame.Rect(300, 300, 500, 30),
        pygame.Rect(150, 450, 200, 30),
        pygame.Rect(750, 450, 200, 30),
    ],
]


def collides(rect, walls):
    for wall in walls:
        if rect.colliderect(wall):
            return True
    return False


class Player:
    def __init__(self, image, gun):
        self.rect = pygame.Rect(100, 300, 15, 15)
        self.image = image
        self.gun = gun
        self.speed = 200
        self.ammo = 100
        self.last = 0
        self.cooldown = 100

    def move(self, keys, walls, dt):
        dx, dy = 0, 0
        if keys[pygame.K_a]:
            dx -= self.speed * dt
        if keys[pygame.K_d]:
            dx += self.speed * dt
        if keys[pygame.K_w]:
            dy -= self.speed * dt
        if keys[pygame.K_s]:
            dy += self.speed * dt

        x = self.rect.x
        self.rect.x += int(dx)
        if collides(self.rect, walls):
            self.rect.x = x

        y = self.rect.y
        self.rect.y += int(dy)
        if collides(self.rect, walls):
            self.rect.y = y

        self.rect.clamp_ip(pygame.Rect(0, 0, *WINDOW_SIZE))

    def draw(self, screen, walls):
        screen.blit(self.image, self.rect.topleft)
        start = self.rect.center
        target = pygame.mouse.get_pos()
        dx, dy = target[0] - start[0], target[1] - start[1]
        dist = math.hypot(dx, dy)

        for i in range(int(dist)):
            x = start[0] + dx * i / dist
            y = start[1] + dy * i / dist
            if collides(pygame.Rect(x, y, 1, 1), walls):
                target = (x, y)
                break

        pygame.draw.line(screen, RED, start, target, 1)
        angle = math.degrees(math.atan2(-dy, dx))
        gun = pygame.transform.rotate(self.gun, angle)
        offset = pygame.Vector2(10, 0).rotate(-angle)
        rect = gun.get_rect(center=(start[0] + offset.x, start[1] + offset.y))
        screen.blit(gun, rect.topleft)

    def can_shoot(self, now):
        return now - self.last >= self.cooldown and self.ammo > 0

    def shoot(self, now):
        self.last = now
        self.ammo -= 1
        x, y = self.rect.center
        mx, my = pygame.mouse.get_pos()
        angle = math.atan2(my - y, mx - x)
        shoot_sound.play()
        return Projectile(x, y, angle)


class Enemy:
    def __init__(self, x, y, red, green):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.hit = False
        self.red = red
        self.green = green

    def draw(self, screen):
        image = self.green if self.hit else self.red
        screen.blit(image, self.rect.topleft)


class Projectile:
    def __init__(self, x, y, angle):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * 700

    def update(self, dt):
        self.pos += self.vel * dt

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (int(self.pos.x), int(self.pos.y)), 3)

    def hits(self, rect):
        return pygame.Rect(self.pos.x, self.pos.y, 3, 3).colliderect(rect)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Vitaprimo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.player_img, self.red_img, self.green_img, self.gun_img = load_images()
        self.walls = self.choose_map()
        self.reset()

    def choose_map(self):
        options = ["1: Map 1", "2: Map 2", "3: Map 3"]
        while True:
            self.screen.fill(BLACK)
            for i in range(len(options)):
                text = self.font.render(options[i], True, WHITE)
                self.screen.blit(text, (50, 100 + i * 50))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_1,
                    pygame.K_2,
                    pygame.K_3,
                ):
                    return MAPS[event.key - pygame.K_1]

    def reset(self):
        self.player = Player(self.player_img, self.gun_img)
        self.enemies = [self.spawn_enemy() for _ in range(5)]
        self.projectiles = []
        self.start = None
        self.end = None
        self.countdown = pygame.time.get_ticks()
        self.game_over = False

    def spawn_enemy(self):
        while True:
            x = random.randint(0, WINDOW_SIZE[0] - 20)
            y = random.randint(0, WINDOW_SIZE[1] - 20)
            enemy = Enemy(x, y, self.red_img, self.green_img)
            if not collides(enemy.rect, self.walls):
                return enemy

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.end:
                self.reset()

    def update(self, dt):
        now = pygame.time.get_ticks()
        if now - self.countdown <= COUNTDOWN_MS:
            return
        if self.start is None:
            self.start = now

        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, dt)

        if pygame.mouse.get_pressed()[0] and self.player.can_shoot(now):
            self.projectiles.append(self.player.shoot(now))

        for projectile in self.projectiles:
            for enemy in self.enemies:
                if not enemy.hit and projectile.hits(enemy.rect):
                    enemy.hit = True

        self.projectiles = [
            projectile
            for projectile in self.projectiles
            if pygame.Rect(0, 0, *WINDOW_SIZE).collidepoint(projectile.pos)
            and not collides(
                pygame.Rect(projectile.pos.x, projectile.pos.y, 3, 3), self.walls
            )
        ]

        for projectile in self.projectiles:
            projectile.update(dt)

        if all(enemy.hit for enemy in self.enemies) and self.end is None:
            self.end = now - self.start

        for enemy in self.enemies:
            if not enemy.hit and self.player.rect.colliderect(enemy.rect):
                self.game_over = True

    def draw_ui(self):
        now = pygame.time.get_ticks()
        time = 0 if self.start is None else (self.end or now - self.start) / 1000
        text = f"Ammo: {self.player.ammo}  Time: {round(time, 2)}s"
        self.screen.blit(self.font.render(text, True, WHITE), (20, 20))

    def draw_win(self):
        msg = f"You win! Time: {round(self.end / 1000, 2)}s - Press R to restart"
        self.screen.blit(self.font.render(msg, True, GREEN), (300, 350))

    def draw_countdown(self):
        now = pygame.time.get_ticks()
        remain = COUNTDOWN_MS - (now - self.countdown)
        if remain > 0:
            sec = math.ceil(remain / 1000)
            label = self.font.render(str(sec), True, RED)
            self.screen.blit(label, (500, 300))

    def render(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, WHITE, pygame.Rect(0, 0, *WINDOW_SIZE), 2)

        for wall in self.walls:
            pygame.draw.rect(self.screen, WHITE, wall)
        self.player.draw(self.screen, self.walls)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for projectile in self.projectiles:
            projectile.draw(self.screen)

        self.draw_ui()
        if self.end:
            self.draw_win()
        self.draw_countdown()
        pygame.display.update()

    def run(self):
        while True:
            dt = self.clock.tick(FRAME_RATE) / 1000
            self.handle_events()
            self.update(dt)
            self.render()


if __name__ == "__main__":
    Game().run()

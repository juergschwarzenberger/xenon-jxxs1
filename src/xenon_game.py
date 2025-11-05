"""Xenon vertical space arcade game implemented with Pygame.

This module provides a playable vertical scrolling shooter featuring
multiple levels, weapons, enemy types, and bosses.  It is designed as a
reference implementation for the "Xenon" concept described in the
repository brief.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, List, Sequence, Tuple

import pygame


# Screen configuration -----------------------------------------------------
WIDTH, HEIGHT = 480, 640
FPS = 60


# Utility types ------------------------------------------------------------
Vector = Tuple[float, float]


@dataclass
class Bullet:
    """Projectile fired by players or enemies."""

    position: Vector
    velocity: Vector
    radius: int
    color: Tuple[int, int, int]
    damage: int
    owner: str

    def update(self, dt: float) -> None:
        x, y = self.position
        vx, vy = self.velocity
        self.position = (x + vx * dt, y + vy * dt)

    def off_screen(self) -> bool:
        x, y = self.position
        return y < -self.radius or y > HEIGHT + self.radius or x < -self.radius or x > WIDTH + self.radius

    def rect(self) -> pygame.Rect:
        x, y = self.position
        return pygame.Rect(int(x - self.radius), int(y - self.radius), self.radius * 2, self.radius * 2)


@dataclass
class Weapon:
    """A weapon controls firing pattern and cooldown."""

    name: str
    cooldown: float
    bullet_speed: float
    damage: int
    pattern: Callable[[Vector], Sequence[float]]
    color: Tuple[int, int, int]
    _cooldown_timer: float = field(default=0.0, init=False)

    def ready(self) -> bool:
        return self._cooldown_timer <= 0

    def update(self, dt: float) -> None:
        if self._cooldown_timer > 0:
            self._cooldown_timer -= dt

    def fire(self, origin: Vector) -> List[Bullet]:
        if not self.ready():
            return []
        self._cooldown_timer = self.cooldown
        bullets = []
        for angle in self.pattern(origin):
            vx = math.cos(angle) * self.bullet_speed
            vy = math.sin(angle) * self.bullet_speed
            bullets.append(
                Bullet(position=origin, velocity=(vx, vy), radius=4, color=self.color, damage=self.damage, owner="player")
            )
        return bullets


@dataclass
class Entity:
    position: Vector
    velocity: Vector
    size: Tuple[int, int]
    color: Tuple[int, int, int]
    health: int
    max_health: int

    def update(self, dt: float) -> None:
        x, y = self.position
        vx, vy = self.velocity
        self.position = (x + vx * dt, y + vy * dt)

    def rect(self) -> pygame.Rect:
        x, y = self.position
        w, h = self.size
        return pygame.Rect(int(x - w / 2), int(y - h / 2), int(w), int(h))

    def take_damage(self, amount: int) -> None:
        self.health -= amount

    def alive(self) -> bool:
        return self.health > 0


class Player(Entity):
    speed: float = 220.0

    def __init__(self, position: Vector, weapons: Sequence[Weapon]):
        super().__init__(position=position, velocity=(0, 0), size=(36, 36), color=(100, 220, 255), health=5, max_health=5)
        self.weapons = list(weapons)
        self.weapon_index = 0
        self.invulnerable_timer = 0.0

    @property
    def weapon(self) -> Weapon:
        return self.weapons[self.weapon_index]

    def grant_weapon(self, index: int) -> None:
        if 0 <= index < len(self.weapons):
            self.weapon_index = index

    def handle_input(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        vx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        vy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.speed
        self.velocity = (vx, vy)
        super().update(dt)
        x, y = self.position
        w, h = self.size
        x = max(w / 2, min(WIDTH - w / 2, x))
        y = max(h / 2, min(HEIGHT - h / 2, y))
        self.position = (x, y)

    def update(self, dt: float) -> None:
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt
        self.weapon.update(dt)

    def shoot(self) -> List[Bullet]:
        return self.weapon.fire((self.position[0], self.position[1] - self.size[1] / 2))

    def take_damage(self, amount: int) -> None:
        if self.invulnerable_timer <= 0:
            super().take_damage(amount)
            self.invulnerable_timer = 1.0


class Enemy(Entity):
    def __init__(self, position: Vector, velocity: Vector, size: Tuple[int, int], color: Tuple[int, int, int], health: int):
        super().__init__(position, velocity, size, color, health, health)
        self.fire_timer = random.uniform(1.0, 3.0)

    def update(self, dt: float) -> None:
        super().update(dt)
        self.fire_timer -= dt

    def should_fire(self) -> bool:
        return self.fire_timer <= 0

    def reset_fire_timer(self) -> None:
        self.fire_timer = random.uniform(1.0, 3.0)

    def fire(self) -> List[Bullet]:
        self.reset_fire_timer()
        vx, vy = 0, 220
        bullet = Bullet(position=(self.position[0], self.position[1] + self.size[1] / 2), velocity=(vx, vy), radius=4,
                        color=(255, 180, 0), damage=1, owner="enemy")
        return [bullet]


class Boss(Enemy):
    def __init__(self, position: Vector, health: int, color: Tuple[int, int, int]):
        super().__init__(position=position, velocity=(0, 40), size=(120, 120), color=color, health=health)
        self.phase = 0
        self.fire_timer = 2.0

    def update(self, dt: float) -> None:
        x, y = self.position
        if y < HEIGHT * 0.25:
            y += 40 * dt
        else:
            self.phase += dt
            x = WIDTH / 2 + math.sin(self.phase) * 140
        self.position = (x, y)
        self.fire_timer -= dt

    def fire(self) -> List[Bullet]:
        self.fire_timer = 0.7
        bullets = []
        for angle in [math.pi / 2 + delta for delta in (-0.4, -0.2, 0, 0.2, 0.4)]:
            vx = math.cos(angle) * 180
            vy = math.sin(angle) * 180
            bullets.append(Bullet(position=self.position, velocity=(vx, vy), radius=6,
                                  color=(255, 50, 50), damage=1, owner="enemy"))
        return bullets


@dataclass
class LevelDefinition:
    name: str
    enemy_color: Tuple[int, int, int]
    enemy_health: int
    enemy_speed: float
    spawn_interval: float
    enemies_to_spawn: int
    boss: Boss
    weapon_index: int


class LevelController:
    def __init__(self, levels: Sequence[LevelDefinition]):
        self.levels = list(levels)
        self.current_level_index = 0
        self.spawn_timer = 0.0
        self.spawned = 0

    @property
    def level(self) -> LevelDefinition:
        return self.levels[self.current_level_index]

    def update(self, dt: float) -> None:
        self.spawn_timer -= dt

    def ready_to_spawn(self) -> bool:
        level = self.level
        return self.spawned < level.enemies_to_spawn and self.spawn_timer <= 0

    def spawn_enemy(self) -> Enemy:
        level = self.level
        x = random.randint(40, WIDTH - 40)
        enemy = Enemy(position=(x, -40), velocity=(0, level.enemy_speed), size=(32, 32),
                      color=level.enemy_color, health=level.enemy_health)
        self.spawned += 1
        self.spawn_timer = level.spawn_interval
        return enemy

    def level_completed(self, enemies: List[Enemy], boss: Boss | None) -> bool:
        level = self.level
        return self.spawned >= level.enemies_to_spawn and not enemies and (boss is None or not boss.alive())

    def next_level(self) -> bool:
        if self.current_level_index + 1 < len(self.levels):
            self.current_level_index += 1
            self.spawn_timer = 1.0
            self.spawned = 0
            return True
        return False


class XenonGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Xenon")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18)

        self.weapons = self._create_weapons()
        levels = self._create_levels()
        self.level_controller = LevelController(levels)

        self.player = Player(position=(WIDTH / 2, HEIGHT - 60), weapons=self.weapons)
        self.player.grant_weapon(levels[0].weapon_index)

        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.enemy_bullets: List[Bullet] = []
        self.boss: Boss | None = None
        self.score = 0
        self.running = True
        self.level_intro_timer = 3.0
        self.game_won = False

    def _create_weapons(self) -> List[Weapon]:
        def single_shot(_: Vector) -> Sequence[float]:
            return [math.pi * -0.5]

        def dual_shot(_: Vector) -> Sequence[float]:
            return [math.radians(-95), math.radians(-85)]

        def spread_shot(_: Vector) -> Sequence[float]:
            return [math.radians(-110), math.radians(-90), math.radians(-70)]

        return [
            Weapon(name="Pulse Cannon", cooldown=0.35, bullet_speed=360, damage=1, pattern=single_shot, color=(80, 200, 255)),
            Weapon(name="Twin Blaster", cooldown=0.30, bullet_speed=380, damage=1, pattern=dual_shot, color=(120, 255, 120)),
            Weapon(name="Spread Shot", cooldown=0.25, bullet_speed=420, damage=1, pattern=spread_shot, color=(255, 180, 80)),
        ]

    def _create_levels(self) -> List[LevelDefinition]:
        bosses = [
            Boss(position=(WIDTH / 2, -120), health=40, color=(180, 60, 60)),
            Boss(position=(WIDTH / 2, -120), health=60, color=(60, 180, 90)),
            Boss(position=(WIDTH / 2, -120), health=80, color=(90, 90, 200)),
        ]
        return [
            LevelDefinition(name="Asteroid Belt", enemy_color=(200, 80, 80), enemy_health=2, enemy_speed=80,
                            spawn_interval=1.5, enemies_to_spawn=12, boss=bosses[0], weapon_index=0),
            LevelDefinition(name="Nebula Skirmish", enemy_color=(80, 200, 120), enemy_health=3, enemy_speed=100,
                            spawn_interval=1.2, enemies_to_spawn=14, boss=bosses[1], weapon_index=1),
            LevelDefinition(name="Quantum Rift", enemy_color=(120, 100, 220), enemy_health=4, enemy_speed=120,
                            spawn_interval=1.0, enemies_to_spawn=16, boss=bosses[2], weapon_index=2),
        ]

    def spawn_boss_if_needed(self) -> None:
        level = self.level_controller.level
        if self.boss is None and self.level_controller.spawned >= level.enemies_to_spawn:
            if level.boss.alive():
                self.boss = level.boss
                self.boss.position = (WIDTH / 2, -120)

    def update(self, dt: float) -> None:
        if self.game_won:
            return

        self.level_controller.update(dt)
        self.player.handle_input(dt)
        self.player.update(dt)

        if self.level_intro_timer > 0:
            self.level_intro_timer -= dt
        else:
            if self.level_controller.ready_to_spawn():
                self.enemies.append(self.level_controller.spawn_enemy())

        self.spawn_boss_if_needed()

        for enemy in list(self.enemies):
            enemy.update(dt)
            if enemy.should_fire():
                self.enemy_bullets.extend(enemy.fire())
            if enemy.position[1] > HEIGHT + 40:
                self.enemies.remove(enemy)

        if self.boss and self.boss.alive():
            self.boss.update(dt)
            if self.boss.fire_timer <= 0:
                self.enemy_bullets.extend(self.boss.fire())
        elif self.boss and not self.boss.alive():
            self.boss = None

        for bullet in list(self.bullets):
            bullet.update(dt)
            if bullet.off_screen():
                self.bullets.remove(bullet)

        for bullet in list(self.enemy_bullets):
            bullet.update(dt)
            if bullet.off_screen():
                self.enemy_bullets.remove(bullet)

        self.handle_collisions()

        level_cleared = self.level_controller.level_completed(self.enemies, self.boss)
        if level_cleared:
            progressed = self.level_controller.next_level()
            if progressed:
                new_weapon_index = self.level_controller.level.weapon_index
                self.player.grant_weapon(new_weapon_index)
                self.level_intro_timer = 3.0
                self.bullets.clear()
                self.enemy_bullets.clear()
                self.enemies.clear()
                self.boss = None
            else:
                self.game_won = True
                self.level_intro_timer = 0
                self.bullets.clear()
                self.enemy_bullets.clear()
                self.enemies.clear()
                self.boss = None

    def handle_collisions(self) -> None:
        for bullet in list(self.bullets):
            if bullet.owner != "player":
                continue
            rect = bullet.rect()
            hit = False
            for enemy in list(self.enemies):
                if rect.colliderect(enemy.rect()):
                    enemy.take_damage(bullet.damage)
                    hit = True
                    if not enemy.alive():
                        self.enemies.remove(enemy)
                        self.score += 100
                    break
            if not hit and self.boss and self.boss.alive() and rect.colliderect(self.boss.rect()):
                self.boss.take_damage(bullet.damage)
                self.score += 150
                hit = True
            if hit:
                self.bullets.remove(bullet)

        player_rect = self.player.rect()
        for bullet in list(self.enemy_bullets):
            if bullet.owner == "enemy" and bullet.rect().colliderect(player_rect):
                self.player.take_damage(1)
                self.enemy_bullets.remove(bullet)

        for enemy in list(self.enemies):
            if enemy.rect().colliderect(player_rect):
                self.player.take_damage(1)
                self.enemies.remove(enemy)

        if self.boss and self.boss.alive() and self.boss.rect().colliderect(player_rect):
            self.player.take_damage(1)

    def draw(self) -> None:
        self.screen.fill((10, 10, 30))

        star_color = (40, 40, 70)
        for y in range(0, HEIGHT, 20):
            pygame.draw.line(self.screen, star_color, (0, y), (WIDTH, y), 1)

        self.draw_entity(self.player)

        for enemy in self.enemies:
            self.draw_entity(enemy)
            self.draw_health_bar(enemy)

        if self.boss and self.boss.alive():
            self.draw_entity(self.boss)
            self.draw_health_bar(self.boss, width=160, offset=80)

        for bullet in self.bullets + self.enemy_bullets:
            pygame.draw.circle(self.screen, bullet.color, (int(bullet.position[0]), int(bullet.position[1])), bullet.radius)

        self.draw_ui()
        pygame.display.flip()

    def draw_entity(self, entity: Entity) -> None:
        rect = entity.rect()
        pygame.draw.rect(self.screen, entity.color, rect, border_radius=6)

    def draw_health_bar(self, entity: Entity, width: int | None = None, offset: int = 24) -> None:
        rect = entity.rect()
        width = width or rect.width
        ratio = max(entity.health, 0) / entity.max_health
        bar_rect = pygame.Rect(rect.centerx - width // 2, rect.top - offset, width, 8)
        pygame.draw.rect(self.screen, (60, 60, 60), bar_rect)
        inner_rect = bar_rect.copy()
        inner_rect.width = max(0, int(bar_rect.width * ratio))
        pygame.draw.rect(self.screen, (60, 220, 80), inner_rect)

    def draw_ui(self) -> None:
        level_name = self.level_controller.level.name
        weapon_name = self.player.weapon.name
        health_text = self.font.render(f"Hull: {self.player.health}/{self.player.max_health}", True, (200, 200, 200))
        weapon_text = self.font.render(f"Weapon: {weapon_name}", True, (200, 200, 200))
        score_text = self.font.render(f"Score: {self.score}", True, (200, 200, 200))
        level_text = self.font.render(f"Level: {level_name}", True, (200, 200, 200))

        self.screen.blit(health_text, (10, HEIGHT - 60))
        self.screen.blit(weapon_text, (10, HEIGHT - 40))
        self.screen.blit(score_text, (10, HEIGHT - 20))
        self.screen.blit(level_text, (WIDTH - level_text.get_width() - 10, 10))

        if self.level_intro_timer > 0:
            intro = self.font.render(f"Entering {level_name}", True, (255, 255, 255))
            self.screen.blit(intro, (WIDTH / 2 - intro.get_width() / 2, HEIGHT / 2))

        if self.game_won:
            victory = self.font.render("Victory!", True, (255, 230, 120))
            info = self.font.render("Press R to play again or Esc to quit", True, (220, 220, 220))
            self.screen.blit(victory, (WIDTH / 2 - victory.get_width() / 2, HEIGHT / 2 - 20))
            self.screen.blit(info, (WIDTH / 2 - info.get_width() / 2, HEIGHT / 2 + 10))
        elif not self.player.alive():
            game_over = self.font.render("Game Over", True, (255, 60, 60))
            self.screen.blit(game_over, (WIDTH / 2 - game_over.get_width() / 2, HEIGHT / 2 - 20))
            restart = self.font.render("Press R to Retry", True, (255, 255, 255))
            self.screen.blit(restart, (WIDTH / 2 - restart.get_width() / 2, HEIGHT / 2 + 10))

    def process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE and not self.game_won:
                    self.bullets.extend(self.player.shoot())
                elif event.key == pygame.K_r and (not self.player.alive() or self.game_won):
                    self.restart()

    def restart(self) -> None:
        self.__init__()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.process_events()
            if self.player.alive():
                self.update(dt)
            else:
                self.player.weapon.update(dt)
            self.draw()
        pygame.quit()


def main() -> None:
    game = XenonGame()
    game.run()


if __name__ == "__main__":
    main()

# ゲーム内エンティティ: プレイヤー・弾・敵
# 位置は全て通路座標 (u, d) で持ち、描画時に射影する

import random
import pygame

from . import assets, config, projection


class Entity:
    """通路座標上のエンティティ共通部分"""

    image_key = ""
    base_width = 0  # 手前(d=0)での表示幅(px)

    def __init__(self, u: float, d: float):
        self.u = u
        self.d = d
        self.alive = True

    def screen_rect(self) -> pygame.Rect:
        """現在位置の描画矩形(足元基準)"""
        x, y = projection.to_screen(self.u, self.d)
        img = assets.get_scaled(self.image_key, self.base_width * projection.scale(self.d))
        rect = img.get_rect(midbottom=(round(x), round(y)))
        return rect

    def draw(self, surface: pygame.Surface) -> None:
        img = assets.get_scaled(self.image_key, self.base_width * projection.scale(self.d))
        x, y = projection.to_screen(self.u, self.d)
        surface.blit(img, img.get_rect(midbottom=(round(x), round(y))))


class Player(Entity):
    image_key = "shooter"
    base_width = config.PLAYER_WIDTH

    def __init__(self):
        super().__init__(u=0.0, d=config.PLAYER_DEPTH)
        self.fire_timer_ms = 0.0

    def update(self, dt_ms: float, mouse_x: float) -> bool:
        """マウスx追随と発射タイマー更新。発射タイミングならTrueを返す"""
        u = projection.u_from_screen_x(mouse_x, self.d)
        self.u = max(-config.U_LIMIT, min(config.U_LIMIT, u))

        self.fire_timer_ms += dt_ms
        if self.fire_timer_ms >= config.FIRE_INTERVAL_MS:
            self.fire_timer_ms -= config.FIRE_INTERVAL_MS
            return True
        return False


class Bullet(Entity):
    image_key = "bullet1"
    base_width = config.BULLET_WIDTH

    def __init__(self, u: float, d: float):
        super().__init__(u, d)
        self.damage = config.BULLET_DAMAGE

    def update(self, dt_ms: float) -> None:
        self.d += config.BULLET_SPEED * dt_ms / 1000
        if self.d >= 1.0:
            self.alive = False


class Enemy(Entity):
    image_key = "enemy1"
    base_width = config.ENEMY_WIDTH

    def __init__(self, u: float):
        super().__init__(u, d=1.0)
        self.hp = config.ENEMY_HP

    def update(self, dt_ms: float) -> None:
        self.d -= config.ENEMY_SPEED * dt_ms / 1000

    def reached_front(self) -> bool:
        """画面最下部(手前端)に到達したか → ゲームオーバー判定"""
        return self.d <= 0.0

    def hit(self, damage: int) -> None:
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False


class EnemySpawner:
    """雑魚1をランダムな間隔・横位置で出現させる"""

    def __init__(self):
        self.timer_ms = 0.0
        self.next_interval_ms = self._roll_interval()

    def _roll_interval(self) -> float:
        jitter = config.ENEMY_SPAWN_JITTER
        return config.ENEMY_SPAWN_INTERVAL_MS * random.uniform(1 - jitter, 1 + jitter)

    def update(self, dt_ms: float) -> Enemy | None:
        self.timer_ms += dt_ms
        if self.timer_ms >= self.next_interval_ms:
            self.timer_ms = 0.0
            self.next_interval_ms = self._roll_interval()
            return Enemy(u=random.uniform(-config.U_LIMIT, config.U_LIMIT))
        return None

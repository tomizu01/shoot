# ゲーム内エンティティ: 味方部隊・弾・敵・アイテム
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
        if self.d > 1.0:  # まだ画面奥に入っていない(隊列の後続など)
            return
        img = assets.get_scaled(self.image_key, self.base_width * projection.scale(self.d))
        x, y = projection.to_screen(self.u, self.d)
        surface.blit(img, img.get_rect(midbottom=(round(x), round(y))))


# --- 味方部隊 ---

# ユニット人数 → (表示幅, 弾の表示幅)
UNIT_SPECS = {
    1: (config.PLAYER_WIDTH, config.BULLET_WIDTH),
    10: (config.PLAYER_WIDTH_X10, config.BULLET_WIDTH_X10),
    100: (config.PLAYER_WIDTH_X100, config.BULLET_WIDTH_X100),
}


class SquadUnit(Entity):
    """味方ユニット(1人/10人分/100人分)。位置はSquadが毎フレーム決める"""

    image_key = "shooter"

    def __init__(self, size: int, u_offset: float):
        super().__init__(u=0.0, d=config.PLAYER_DEPTH)
        self.size = size              # 1 | 10 | 100
        self.u_offset = u_offset      # 部隊中心からのずれ(u座標)
        self.base_width = UNIT_SPECS[size][0]


class Squad:
    """味方部隊全体。総数を100人/10人/1人ユニットに分解して横に並べる"""

    def __init__(self):
        self.count = 1
        self.attack_power = 1
        self.d = config.PLAYER_DEPTH
        self.center_u = 0.0
        self.fire_timer_ms = 0.0
        self.units: list[SquadUnit] = []
        self._rebuild_units()

    def set_count(self, n: int) -> None:
        new_count = max(1, min(config.SQUAD_MAX, n))
        if new_count != self.count:
            self.count = new_count
            self._rebuild_units()

    def _rebuild_units(self) -> None:
        """総数をユニットに分解し、中央から外側へ交互に並べる"""
        sizes = (
            [100] * (self.count // 100)
            + [10] * (self.count % 100 // 10)
            + [1] * (self.count % 10)
        )
        # 大きいユニットが中央に来るよう、中央から左右交互に詰めて配置(px単位)
        placements: list[tuple[int, float]] = []  # (size, center_px)
        left_px = right_px = 0.0
        for i, size in enumerate(sizes):
            w = UNIT_SPECS[size][0] * config.UNIT_OVERLAP
            if i == 0:
                center_px = 0.0
                left_px, right_px = -w / 2, w / 2
            elif i % 2 == 1:
                center_px = right_px + w / 2
                right_px += w
            else:
                center_px = left_px - w / 2
                left_px -= w
            placements.append((size, center_px))

        # 交互配置は偶数個で左右非対称になるため、隊列の中点を0に補正する
        # (左右どちらに寄せても端のユニットが同じだけ壁に近づけるように)
        mid_px = (left_px + right_px) / 2
        placements = [(size, px - mid_px) for size, px in placements]

        # 部隊全体の幅を画面横幅の一定割合に制限。超える場合は間隔を詰めて重ねる
        span_px = right_px - left_px
        max_px = config.SCREEN_WIDTH * config.SQUAD_MAX_WIDTH_RATIO
        if span_px > max_px:
            shrink = max_px / span_px
            placements = [(size, px * shrink) for size, px in placements]

        half_corridor = projection.corridor_width(self.d) / 2
        self.units = [
            SquadUnit(size, center_px / half_corridor) for size, center_px in placements
        ]
        # 部隊全体が通路に収まるよう中心位置の可動範囲を決める
        max_extent = max(abs(u.u_offset) for u in self.units)
        self.center_limit = max(0.0, config.U_LIMIT - max_extent)

    def update(self, dt_ms: float, mouse_x: float) -> list["Bullet"]:
        """マウス追随と一斉射撃。発射タイミングなら弾のリストを返す"""
        u = projection.u_from_screen_x(mouse_x, self.d)
        self.center_u = max(-self.center_limit, min(self.center_limit, u))
        for unit in self.units:
            unit.u = self.center_u + unit.u_offset

        self.fire_timer_ms += dt_ms
        if self.fire_timer_ms >= config.FIRE_INTERVAL_MS:
            self.fire_timer_ms -= config.FIRE_INTERVAL_MS
            return [self._make_bullet(unit) for unit in self.units]
        return []

    def _make_bullet(self, unit: SquadUnit) -> "Bullet":
        # グループユニットと攻撃力上昇後はパワーアップ弾(bullet2)で表現
        powered = unit.size > 1 or self.attack_power > 1
        return Bullet(
            u=unit.u,
            d=self.d,
            damage=unit.size * self.attack_power,
            image_key="bullet2" if powered else "bullet1",
            base_width=UNIT_SPECS[unit.size][1],
        )

    def draw(self, surface: pygame.Surface) -> None:
        for unit in self.units:
            unit.draw(surface)


# --- 弾 ---


class Bullet(Entity):
    def __init__(self, u: float, d: float, damage: int = config.BULLET_DAMAGE,
                 image_key: str = "bullet1", base_width: int = config.BULLET_WIDTH):
        super().__init__(u, d)
        self.damage = damage
        self.image_key = image_key
        self.base_width = base_width

    def update(self, dt_ms: float) -> None:
        self.d += config.BULLET_SPEED * projection.depth_speed_factor(self.d) * dt_ms / 1000
        if self.d >= 1.0:
            self.alive = False


# --- 敵 ---


class Enemy(Entity):
    """雑魚。ボスはこれを継承する"""

    image_key = "enemy1"
    base_width = config.ENEMY_WIDTH
    speed = config.ENEMY_SPEED

    def __init__(self, u: float, d: float = 1.0, hp: int = config.ENEMY_HP):
        super().__init__(u, d)
        self.hp = hp

    def update(self, dt_ms: float) -> None:
        # 画面奥(d>1)にいる間は遠近補正をかけずに進める
        factor = projection.depth_speed_factor(self.d) if self.d <= 1.0 else 1.0
        self.d -= self.speed * factor * dt_ms / 1000

    def reached_front(self) -> bool:
        """画面最下部(手前端)に到達したか → ゲームオーバー判定"""
        return self.d <= 0.0

    def hit(self, damage: int) -> None:
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False


class MidBoss(Enemy):
    """中ボス(e2)。耐久はステージCSVで指定、残り耐久を表示する"""

    image_key = "enemy2"
    base_width = config.ENEMY2_WIDTH
    speed = config.ENEMY2_SPEED

    def label(self) -> str:
        return str(self.hp)


class BigBoss(Enemy):
    """大ボス(e3)。耐久はステージCSVで指定、残り耐久を表示する"""

    image_key = "enemy3"
    base_width = config.ENEMY3_WIDTH
    speed = config.ENEMY3_SPEED

    def label(self) -> str:
        return str(self.hp)


# --- アイテム ---


class Item(Entity):
    """降下するアイテムの共通部分。画面下に抜けても(ゲームオーバーにならず)消えるだけ"""

    def __init__(self, u: float):
        super().__init__(u, d=1.0)

    def update(self, dt_ms: float) -> None:
        self.d -= config.ITEM_SPEED * projection.depth_speed_factor(self.d) * dt_ms / 1000
        if self.d <= 0.0:
            self.alive = False

    def label(self) -> str:
        raise NotImplementedError


class PanelAdd(Item):
    """+n パネル: 味方が接触すると人数が n 増える"""

    image_key = "powerup1"
    base_width = config.PANEL_WIDTH

    def __init__(self, u: float, n: int | None = None):
        super().__init__(u)
        self.n = n if n is not None else random.randint(
            config.PANEL_ADD_MIN, config.PANEL_ADD_MAX
        )

    def label(self) -> str:
        return f"+{self.n}"

    def apply(self, squad: Squad) -> None:
        squad.set_count(squad.count + self.n)


class PanelMul(Item):
    """×n パネル: 味方が接触すると人数が n 倍になる"""

    image_key = "powerup2"
    base_width = config.PANEL_WIDTH

    def __init__(self, u: float, n: int | None = None):
        super().__init__(u)
        self.n = n if n is not None else random.randint(
            config.PANEL_MUL_MIN, config.PANEL_MUL_MAX
        )

    def label(self) -> str:
        return f"×{self.n}"

    def apply(self, squad: Squad) -> None:
        squad.set_count(squad.count * self.n)


class ItemBox(Item):
    """アイテムボックス: 弾で破壊すると攻撃力+1。未破壊のまま味方に接触すると味方半減"""

    image_key = "powerup3"
    base_width = config.BOX_WIDTH

    def __init__(self, u: float, hp: int | None = None):
        super().__init__(u)
        self.hp = hp if hp is not None else random.randint(
            config.BOX_HP_MIN, config.BOX_HP_MAX
        )

    def label(self) -> str:
        return str(self.hp)

    def hit(self, damage: int) -> bool:
        """弾が命中。破壊されたらTrueを返す"""
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def apply(self, squad: Squad) -> None:
        """未破壊のまま味方に接触 → 味方が 1/BOX_PENALTY_DIV に減る"""
        squad.set_count(squad.count // config.BOX_PENALTY_DIV)


# 出現管理はステージCSV駆動(game/stage.py)に移行した。
# ランダム出現が必要になったら git履歴の Spawner クラスを参照。

# ゲームループと状態管理

import pygame

from . import assets, config
from .entities import Bullet, Enemy, EnemySpawner, Player

STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"


class Game:
    def __init__(self, smoke_frames: int = 0):
        pygame.init()
        # ゲームは論理解像度(1086x1448)のサーフェスに描画し、
        # 毎フレームwindowサイズに合わせて拡縮表示する(手動スケーリング方式)
        # ※ pygame.SCALED|RESIZABLE はWindowsでリサイズできない問題があるため不使用
        desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
        init_scale = min(
            desktop_w * 0.9 / config.SCREEN_WIDTH,
            desktop_h * 0.9 / config.SCREEN_HEIGHT,
            1.0,
        )
        init_size = (
            round(config.SCREEN_WIDTH * init_scale),
            round(config.SCREEN_HEIGHT * init_scale),
        )
        self.window = pygame.display.set_mode(init_size, pygame.RESIZABLE)
        self.screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self._update_viewport()
        pygame.display.set_caption(config.CAPTION)
        pygame.mouse.set_visible(False)
        assets.load_all()

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("meiryo", config.HUD_FONT_SIZE, bold=True)
        self.big_font = pygame.font.SysFont("meiryo", config.HUD_FONT_SIZE * 2, bold=True)
        self.smoke_frames = smoke_frames  # 動作確認用: 指定フレーム数で自動終了

        self.reset()

    def reset(self) -> None:
        self.state = STATE_PLAYING
        self.player = Player()
        self.bullets: list[Bullet] = []
        self.enemies: list[Enemy] = []
        self.spawner = EnemySpawner()
        self.score = 0

    # --- ウィンドウスケーリング ---

    def _update_viewport(self) -> None:
        """ウィンドウ内で論理画面を表示する領域(縦横比維持・レターボックス)を計算"""
        win_w, win_h = self.window.get_size()
        self.view_scale = min(win_w / config.SCREEN_WIDTH, win_h / config.SCREEN_HEIGHT)
        view_w = round(config.SCREEN_WIDTH * self.view_scale)
        view_h = round(config.SCREEN_HEIGHT * self.view_scale)
        self.view_offset = ((win_w - view_w) // 2, (win_h - view_h) // 2)
        self.view_size = (view_w, view_h)

    def mouse_logical_x(self) -> float:
        """ウィンドウ上のマウスx座標 → 論理画面のx座標"""
        mx, _ = pygame.mouse.get_pos()
        return (mx - self.view_offset[0]) / self.view_scale

    # --- メインループ ---

    def run(self) -> None:
        frame = 0
        running = True
        while running:
            dt_ms = self.clock.tick(config.FPS)
            running = self.handle_events()
            if self.state == STATE_PLAYING:
                self.update(dt_ms)
            self.draw()
            # 論理画面をウィンドウサイズに拡縮して表示
            self.window.fill((0, 0, 0))
            scaled = pygame.transform.smoothscale(self.screen, self.view_size)
            self.window.blit(scaled, self.view_offset)
            pygame.display.flip()

            frame += 1
            if self.smoke_frames and frame >= self.smoke_frames:
                pygame.image.save(self.screen, "smoke.png")  # 動作確認用キャプチャ
                running = False
        pygame.quit()

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r and self.state == STATE_GAME_OVER:
                    self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and self.state == STATE_GAME_OVER:
                self.reset()
            if event.type == pygame.VIDEORESIZE:
                self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                self._update_viewport()
        return True

    # --- 更新 ---

    def update(self, dt_ms: float) -> None:
        mouse_x = self.mouse_logical_x()

        # プレイヤー: マウス追随 + 自動発射
        if self.player.update(dt_ms, mouse_x):
            self.bullets.append(Bullet(self.player.u, self.player.d))

        # 弾
        for bullet in self.bullets:
            bullet.update(dt_ms)

        # 敵: 出現と前進
        spawned = self.spawner.update(dt_ms)
        if spawned:
            self.enemies.append(spawned)
        for enemy in self.enemies:
            enemy.update(dt_ms)
            if enemy.reached_front():
                self.state = STATE_GAME_OVER
                return

        # 弾と敵の当たり判定
        self.resolve_hits()

        self.bullets = [b for b in self.bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]

    def resolve_hits(self) -> None:
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                # 奥行きがほぼ一致し、画面上の矩形が重なれば命中
                if abs(bullet.d - enemy.d) > config.HIT_DEPTH_RANGE:
                    continue
                if bullet.screen_rect().colliderect(enemy.screen_rect()):
                    enemy.hit(bullet.damage)
                    bullet.alive = False
                    if not enemy.alive:
                        self.score += 1
                    break

    # --- 描画 ---

    def draw(self) -> None:
        self.screen.blit(assets.get("bg"), (0, 0))

        # 奥のものから順に描く(手前のスプライトが上に重なる)
        drawables = sorted(
            [*self.enemies, *self.bullets], key=lambda e: e.d, reverse=True
        )
        for entity in drawables:
            entity.draw(self.screen)
        self.player.draw(self.screen)

        self.draw_hud()
        if self.state == STATE_GAME_OVER:
            self.draw_game_over()

    def draw_text(self, text: str, center: tuple[int, int], font=None) -> None:
        font = font or self.font
        shadow = font.render(text, True, config.HUD_SHADOW)
        surface = font.render(text, True, config.HUD_COLOR)
        rect = surface.get_rect(center=center)
        self.screen.blit(shadow, rect.move(3, 3))
        self.screen.blit(surface, rect)

    def draw_hud(self) -> None:
        self.draw_text(f"SCORE {self.score}", (config.SCREEN_WIDTH // 2, 40))

    def draw_game_over(self) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        cx = config.SCREEN_WIDTH // 2
        cy = config.SCREEN_HEIGHT // 2
        self.draw_text("GAME OVER", (cx, cy - 60), self.big_font)
        self.draw_text("クリック / Rキー でリスタート", (cx, cy + 60))

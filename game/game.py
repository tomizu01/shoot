# ゲームループと状態管理

import pygame

from . import assets, config, stage
from .entities import Bullet, Enemy, Item, ItemBox, Squad

STATE_STAGE_SELECT = "stage_select"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_STAGE_CLEAR = "stage_clear"


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
        self.label_font = pygame.font.SysFont("meiryo", 36, bold=True)
        self.smoke_frames = smoke_frames  # 動作確認用: 指定フレーム数で自動終了

        self.select_buttons = self._build_select_buttons()
        self.start_run(config.STAGE_FIRST)  # ゲーム用属性の初期化を兼ねる
        if not smoke_frames:
            self.goto_stage_select()  # 通常起動はステージ選択画面から

    # --- ステージ選択 ---

    def _build_select_buttons(self) -> list[tuple[pygame.Rect, int]]:
        """存在するステージのボタンを2列グリッドで配置(論理座標)"""
        numbers = stage.list_stages()
        cols = 2
        bw, bh, gap = 380, 110, 40
        grid_w = cols * bw + (cols - 1) * gap
        x0 = (config.SCREEN_WIDTH - grid_w) // 2
        y0 = 420
        buttons = []
        for i, n in enumerate(numbers):
            col, row = i % cols, i // cols
            rect = pygame.Rect(x0 + col * (bw + gap), y0 + row * (bh + gap), bw, bh)
            buttons.append((rect, n))
        return buttons

    def goto_stage_select(self) -> None:
        self.state = STATE_STAGE_SELECT
        pygame.mouse.set_visible(True)

    def start_run(self, number: int) -> None:
        """選択したステージから新規プレイ開始(味方・スコア初期化)"""
        self.squad = Squad()
        self.score = 0
        self.start_stage(number)
        pygame.mouse.set_visible(False)

    def start_stage(self, number: int) -> None:
        """指定ステージを開始。味方人数は持ち越し、攻撃力はリセット"""
        self.state = STATE_PLAYING
        self.stage = stage.StageManager(number)
        self.squad.attack_power = 1
        self.bullets: list[Bullet] = []
        self.enemies: list[Enemy] = []
        self.items: list[Item] = []
        self.clear_timer_ms = 0.0

    # --- ウィンドウスケーリング ---

    def _update_viewport(self) -> None:
        """ウィンドウ内で論理画面を表示する領域(縦横比維持・レターボックス)を計算"""
        win_w, win_h = self.window.get_size()
        self.view_scale = min(win_w / config.SCREEN_WIDTH, win_h / config.SCREEN_HEIGHT)
        view_w = round(config.SCREEN_WIDTH * self.view_scale)
        view_h = round(config.SCREEN_HEIGHT * self.view_scale)
        self.view_offset = ((win_w - view_w) // 2, (win_h - view_h) // 2)
        self.view_size = (view_w, view_h)

    def to_logical_pos(self, window_pos: tuple[int, int]) -> tuple[float, float]:
        """ウィンドウ座標 → 論理画面座標"""
        return (
            (window_pos[0] - self.view_offset[0]) / self.view_scale,
            (window_pos[1] - self.view_offset[1]) / self.view_scale,
        )

    def mouse_logical_x(self) -> float:
        """ウィンドウ上のマウスx座標 → 論理画面のx座標"""
        return self.to_logical_pos(pygame.mouse.get_pos())[0]

    # --- メインループ ---

    def run(self) -> None:
        frame = 0
        running = True
        while running:
            dt_ms = self.clock.tick(config.FPS)
            running = self.handle_events()
            if self.state == STATE_PLAYING:
                self.update(dt_ms)
            elif self.state == STATE_STAGE_CLEAR:
                self.update_stage_clear(dt_ms)
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
                    self.goto_stage_select()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == STATE_GAME_OVER:
                    self.goto_stage_select()
                elif self.state == STATE_STAGE_SELECT:
                    pos = self.to_logical_pos(event.pos)
                    for rect, number in self.select_buttons:
                        if rect.collidepoint(pos):
                            self.start_run(number)
                            break
            if event.type == pygame.VIDEORESIZE:
                self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                self._update_viewport()
        return True

    # --- 更新 ---

    def update(self, dt_ms: float) -> None:
        mouse_x = self.mouse_logical_x()

        # 味方部隊: マウス追随 + 一斉射撃
        self.bullets.extend(self.squad.update(dt_ms, mouse_x))

        # 弾
        for bullet in self.bullets:
            bullet.update(dt_ms)

        # 敵・アイテム: ステージ進行に応じて出現、前進
        for spawned in self.stage.update(dt_ms):
            if isinstance(spawned, Enemy):
                self.enemies.append(spawned)
            else:
                self.items.append(spawned)
        for enemy in self.enemies:
            enemy.update(dt_ms)
            if enemy.reached_front():
                self.state = STATE_GAME_OVER
                return
        for item in self.items:
            item.update(dt_ms)

        # 当たり判定
        self.resolve_bullet_hits()
        self.resolve_item_pickups()

        self.bullets = [b for b in self.bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        self.items = [i for i in self.items if i.alive]

        # ステージクリア判定: 全イベント発生済み+猶予進行+敵全滅
        if self.stage.reached_end() and not self.enemies:
            self.state = STATE_STAGE_CLEAR
            self.clear_timer_ms = 0.0

    def update_stage_clear(self, dt_ms: float) -> None:
        """「STAGE CLEAR」表示後、ステージ選択画面に戻る
        (次のプレイは常に1人・パワーアップ無しから)"""
        self.clear_timer_ms += dt_ms
        if self.clear_timer_ms >= config.STAGE_CLEAR_WAIT_MS:
            self.goto_stage_select()

    def resolve_bullet_hits(self) -> None:
        """弾 vs 敵・アイテムボックス(パネルは弾が素通りする)"""
        boxes = [i for i in self.items if isinstance(i, ItemBox)]
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            for target in [*self.enemies, *boxes]:
                if not target.alive:
                    continue
                # 奥行きがほぼ一致し、画面上の矩形が重なれば命中
                if abs(bullet.d - target.d) > config.HIT_DEPTH_RANGE:
                    continue
                if bullet.screen_rect().colliderect(target.screen_rect()):
                    bullet.alive = False
                    if isinstance(target, Enemy):
                        target.hit(bullet.damage)
                        if not target.alive:
                            self.score += 1
                    elif target.hit(bullet.damage):  # ItemBox 破壊
                        self.squad.attack_power += config.BOX_ATTACK_BONUS
                    break

    def resolve_item_pickups(self) -> None:
        """味方の列に到達したアイテムと味方ユニットの接触判定"""
        unit_rects = [unit.screen_rect() for unit in self.squad.units]
        for item in self.items:
            if not item.alive:
                continue
            # 味方の奥行きまで降りてきたものだけ判定
            if item.d > self.squad.d + config.HIT_DEPTH_RANGE:
                continue
            item_rect = item.screen_rect()
            if any(item_rect.colliderect(r) for r in unit_rects):
                item.apply(self.squad)  # パネル=増加 / 未破壊ボックス=半減
                item.alive = False

    # --- 描画 ---

    def draw(self) -> None:
        self.screen.blit(assets.get("bg"), (0, 0))

        if self.state == STATE_STAGE_SELECT:
            self.draw_stage_select()
            return

        # 奥のものから順に描く(手前のスプライトが上に重なる)
        drawables = sorted(
            [*self.enemies, *self.items, *self.bullets], key=lambda e: e.d, reverse=True
        )
        for entity in drawables:
            entity.draw(self.screen)
        self.squad.draw(self.screen)

        # 数値ラベル(アイテムの+n/×n/耐久、ボスの残り耐久)
        for obj in [*self.items, *self.enemies]:
            if hasattr(obj, "label") and obj.d <= 1.0:
                rect = obj.screen_rect()
                self.draw_text(obj.label(), rect.center, self.label_font)

        self.draw_hud()
        if self.state == STATE_GAME_OVER:
            self.draw_game_over()
        elif self.state == STATE_STAGE_CLEAR:
            self.draw_center_message(f"STAGE {self.stage.number} CLEAR!")

    def draw_text(self, text: str, center: tuple[int, int], font=None) -> None:
        font = font or self.font
        shadow = font.render(text, True, config.HUD_SHADOW)
        surface = font.render(text, True, config.HUD_COLOR)
        rect = surface.get_rect(center=center)
        self.screen.blit(shadow, rect.move(3, 3))
        self.screen.blit(surface, rect)

    def draw_hud(self) -> None:
        text = (
            f"STAGE {self.stage.number}   "
            f"SCORE {self.score}   "
            f"味方 {self.squad.count}   "
            f"攻撃力 {self.squad.attack_power}"
        )
        self.draw_text(text, (config.SCREEN_WIDTH // 2, 40))
        # 性能確認用FPS(右上、HUD本体と重ならない位置)
        fps = f"FPS {self.clock.get_fps():.0f}"
        self.draw_text(fps, (config.SCREEN_WIDTH - 90, 100), self.label_font)

    def draw_stage_select(self) -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 30, 170))
        self.screen.blit(overlay, (0, 0))
        cx = config.SCREEN_WIDTH // 2
        self.draw_text("STAGE SELECT", (cx, 240), self.big_font)
        self.draw_text("ステージを選んでください", (cx, 340))

        mouse_pos = self.to_logical_pos(pygame.mouse.get_pos())
        for rect, number in self.select_buttons:
            hover = rect.collidepoint(mouse_pos)
            fill = (90, 110, 160) if hover else (40, 50, 80)
            pygame.draw.rect(self.screen, fill, rect, border_radius=16)
            pygame.draw.rect(self.screen, (200, 210, 230), rect, width=3, border_radius=16)
            self.draw_text(f"STAGE {number}", rect.center)

    def draw_game_over(self) -> None:
        self.draw_center_message("GAME OVER", "クリック / Rキー でステージ選択へ")

    def draw_center_message(self, title: str, subtitle: str = "") -> None:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        cx = config.SCREEN_WIDTH // 2
        cy = config.SCREEN_HEIGHT // 2
        self.draw_text(title, (cx, cy - 60), self.big_font)
        if subtitle:
            self.draw_text(subtitle, (cx, cy + 60))

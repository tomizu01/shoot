# ゲーム全体の調整パラメータ
# 改良提案で数値をいじる場合は基本的にこのファイルを変更する

# --- 画面 ---
SCREEN_WIDTH = 1086     # 背景画像 bg2.png の実寸に合わせる
SCREEN_HEIGHT = 1448
FPS = 60
CAPTION = "Multi Shooter"

# --- 疑似3D通路 ---
# 通路座標系: u = 横位置 (-1.0=左端, +1.0=右端), d = 奥行き (0.0=手前, 1.0=奥)
CORRIDOR_WIDTH_FRONT = 1086   # 手前の通路幅(px)
CORRIDOR_WIDTH_BACK = 300     # 奥の通路幅(px)
CORRIDOR_Y_FRONT = 1448       # 手前端の画面y座標
CORRIDOR_Y_BACK = 60          # 奥端の画面y座標
U_LIMIT = 0.85                # 壁にめり込まないための横移動制限

# --- プレイヤー ---
PLAYER_WIDTH = 100            # 手前(d=0)での表示幅(px)
PLAYER_DEPTH = 0.02           # プレイヤーの立ち位置(奥行き)
FIRE_INTERVAL_MS = 250        # 発射間隔(ミリ秒)

# --- 弾 ---
BULLET_WIDTH = 26             # 手前での表示幅(px)
BULLET_SPEED = 1.2            # 奥行き速度(d/秒)。1.2なら約0.83秒で奥に到達
BULLET_DAMAGE = 1

# --- 敵(雑魚1) ---
ENEMY_WIDTH = 120             # 手前での表示幅(px)
ENEMY_SPEED = 0.15            # 奥行き速度(d/秒)。0.15なら約6.7秒で手前に到達
ENEMY_HP = 1
ENEMY_SPAWN_INTERVAL_MS = 900 # 平均出現間隔(ミリ秒)
ENEMY_SPAWN_JITTER = 0.5      # 出現間隔のゆらぎ(0.5なら±50%)

# --- 当たり判定 ---
HIT_DEPTH_RANGE = 0.04        # 弾と敵の奥行き一致とみなす範囲

# --- HUD ---
HUD_FONT_SIZE = 48
HUD_COLOR = (255, 255, 255)
HUD_SHADOW = (0, 0, 0)

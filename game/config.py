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
DEPTH_SPEED_GAMMA = 2.0       # 手前加速の強さ(1.0=弱い、上げるほど手前で加速)
DEPTH_SPEED_REF_D = 0.65      # 速度基準の奥行き(γ変更時のトータル所要時間調整用)

# --- プレイヤー(味方部隊) ---
PLAYER_WIDTH = 100            # 1人ユニットの手前(d=0)での表示幅(px)
PLAYER_WIDTH_X10 = 135        # 10人ユニットの表示幅(少し拡大)
PLAYER_WIDTH_X100 = 175       # 100人ユニットの表示幅(さらに拡大)
PLAYER_DEPTH = 0.02           # プレイヤーの立ち位置(奥行き)
FIRE_INTERVAL_MS = 250        # 発射間隔(ミリ秒)
SQUAD_MAX = 1000              # 味方の最大人数
UNIT_OVERLAP = 0.6            # 横並びの詰め具合(1.0=密着、小さいほど重なる)
SQUAD_MAX_WIDTH_RATIO = 0.25  # 部隊の最大幅(画面横幅に対する割合)。超えたら詰めて重ねる

# --- 弾 ---
BULLET_WIDTH = 26             # 手前での表示幅(px)
BULLET_WIDTH_X10 = 40         # 10人ユニットの弾の表示幅
BULLET_WIDTH_X100 = 56        # 100人ユニットの弾の表示幅
BULLET_SPEED = 1.2            # 奥行き速度(d/秒)。1.2なら約0.83秒で奥に到達
BULLET_DAMAGE = 1

# --- アイテム ---
ITEM_SPEED = 0.05             # アイテムの降下速度(d/秒)
PANEL_WIDTH = 140             # パネルの手前での表示幅(px)
BOX_WIDTH = 140               # アイテムボックスの表示幅(px)
PANEL_ADD_MIN = 1             # +n パネルの範囲
PANEL_ADD_MAX = 10
PANEL_MUL_MIN = 2             # ×n パネルの範囲
PANEL_MUL_MAX = 5
BOX_HP_MIN = 5                # ボックスの耐久範囲
BOX_HP_MAX = 15
BOX_ATTACK_BONUS = 1          # ボックス破壊時の攻撃力上昇
BOX_PENALTY_DIV = 2           # 未破壊ボックス接触時に味方が 1/n になる

# --- ステージ ---
STAGE_DIR = "stages"            # ステージCSVの場所(stage1.csv, stage2.csv, ...)
STAGE_FIRST = 1                 # 開始ステージ番号
STAGE_PROGRESS_PER_SEC = 100    # 進行距離/秒(CSVの登場タイミングの基準)
STAGE_CLEAR_BUFFER = 300        # 最終イベント後、クリア判定を始めるまでの進行距離
STAGE_CLEAR_WAIT_MS = 2500      # 「STAGE CLEAR」表示の時間
LANE_U = {1: -0.75, 2: -0.25, 3: 0.25, 4: 0.75}  # レーン番号 → 横位置u
ZAKO_CLUSTER_JITTER_U = 0.15    # e1複数体の横ばらつき(レーン内)
ZAKO_CLUSTER_STEP_D = 0.04      # e1複数体の奥行きずらし(隊列で降りてくる)

# --- 敵(雑魚1) ---
ENEMY_WIDTH = 120             # 手前での表示幅(px)
ENEMY_SPEED = 0.05            # 奥行き速度(d/秒)。0.05なら約20秒で手前に到達
ENEMY_HP = 1

# --- 中ボス(e2)/大ボス(e3) 耐久はステージCSVで指定 ---
ENEMY2_WIDTH = 220
ENEMY2_SPEED = 0.035
ENEMY3_WIDTH = 680            # 2レーン分を占有する迫力サイズ
ENEMY3_SPEED = 0.025

# --- 当たり判定 ---
HIT_DEPTH_RANGE = 0.04        # 弾と敵の奥行き一致とみなす範囲

# --- HUD ---
HUD_FONT_SIZE = 48
HUD_COLOR = (255, 255, 255)
HUD_SHADOW = (0, 0, 0)

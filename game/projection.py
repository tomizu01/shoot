# 疑似3D射影
# ゲームロジックは通路座標 (u, d) で扱い、描画時のみ画面座標へ変換する
#   u: 横位置 (-1.0=通路左端, 0=中央, +1.0=通路右端)
#   d: 奥行き (0.0=手前, 1.0=奥)

from . import config


def corridor_width(d: float) -> float:
    """奥行きdでの通路幅(px)"""
    return config.CORRIDOR_WIDTH_FRONT + (
        config.CORRIDOR_WIDTH_BACK - config.CORRIDOR_WIDTH_FRONT
    ) * d


def scale(d: float) -> float:
    """奥行きdでのスプライト縮尺(手前=1.0)"""
    return corridor_width(d) / config.CORRIDOR_WIDTH_FRONT


def depth_speed_factor(d: float) -> float:
    """遠近感に合わせた奥行き速度の補正係数。

    スプライトの見た目の大きさ(scale)の比のγ乗で画面上の移動速度を変えることで、
    「手前に来るほど加速して見える」遠近の動きになる。
    γ(DEPTH_SPEED_GAMMA)を上げるほど手前の加速が強くなる。
    基準点(DEPTH_SPEED_REF_D)は奥→手前のトータル所要時間が
    補正なしの場合とほぼ同じになるよう調整してある。
    """
    return (scale(d) / scale(config.DEPTH_SPEED_REF_D)) ** config.DEPTH_SPEED_GAMMA


def to_screen(u: float, d: float) -> tuple[float, float]:
    """通路座標(u, d) → 画面座標(x, y)"""
    x = config.SCREEN_WIDTH / 2 + u * corridor_width(d) / 2
    y = config.CORRIDOR_Y_FRONT + (config.CORRIDOR_Y_BACK - config.CORRIDOR_Y_FRONT) * d
    return x, y


def u_from_screen_x(x: float, d: float) -> float:
    """画面x座標 → 奥行きdでのu座標(マウス追随用)"""
    half = corridor_width(d) / 2
    if half <= 0:
        return 0.0
    return (x - config.SCREEN_WIDTH / 2) / half

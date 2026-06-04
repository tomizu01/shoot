# 画像の読み込みと、奥行きスケール済みスプライトのキャッシュ

import os
import pygame

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "sozai", "images")

IMAGE_FILES = {
    "bg": "bg2.png",
    "bullet1": "bullet1.png",
    "bullet2": "bullet2.png",
    "enemy1": "enemy1.png",
    "enemy2": "enemy2.png",
    "enemy3": "enemy3.png",
    "powerup1": "powerup1.png",
    "powerup2": "powerup2.png",
    "powerup3": "powerup3.png",
    "shooter": "shooter.png",
}

_images: dict[str, pygame.Surface] = {}
_scaled_cache: dict[tuple[str, int], pygame.Surface] = {}


def load_all() -> None:
    """全画像を読み込む。display初期化後に一度だけ呼ぶ"""
    for key, filename in IMAGE_FILES.items():
        path = os.path.join(IMAGE_DIR, filename)
        _images[key] = pygame.image.load(path).convert_alpha()


def get(key: str) -> pygame.Surface:
    return _images[key]


def get_scaled(key: str, width: float) -> pygame.Surface:
    """指定幅にスケールした画像を返す(アスペクト比維持・キャッシュあり)

    幅を4px単位に丸めてキャッシュすることで、毎フレームのsmoothscaleを避ける。
    将来味方や弾が大量になっても描画負荷を抑えられる。
    """
    w = max(4, int(width) // 4 * 4)
    cache_key = (key, w)
    cached = _scaled_cache.get(cache_key)
    if cached is not None:
        return cached
    src = _images[key]
    h = max(1, round(src.get_height() * w / src.get_width()))
    scaled = pygame.transform.smoothscale(src, (w, h))
    _scaled_cache[cache_key] = scaled
    return scaled

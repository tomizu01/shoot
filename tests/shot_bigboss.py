# 大ボスの見た目確認用スクリーンショット生成(ヘッドレス)
# 実行: python tests/shot_bigboss.py → tests/bigboss.png

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402
from game.entities import BigBoss, Enemy, MidBoss  # noqa: E402
from game.game import Game  # noqa: E402


def main():
    game = Game()
    game.squad.set_count(35)
    # レーン2指定の大ボス(u=0)が降りてきた場面を再現
    boss = BigBoss(u=0.0, hp=1000)
    boss.d = 0.45
    mid = MidBoss(u=-0.75, hp=300)
    mid.d = 0.7
    game.enemies = [boss, mid, Enemy(u=0.6, d=0.25), Enemy(u=-0.4, d=0.15)]
    game.draw()
    out = os.path.join(os.path.dirname(__file__), "bigboss.png")
    pygame.image.save(game.screen, out)
    print("saved:", out)


if __name__ == "__main__":
    main()

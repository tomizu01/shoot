# ステージ選択画面の見た目確認用スクリーンショット生成(ヘッドレス)
# 実行: python tests/shot_select.py → tests/select.png

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402
from game.game import Game  # noqa: E402


def main():
    game = Game()  # 通常起動 → ステージ選択画面
    game.draw()
    out = os.path.join(os.path.dirname(__file__), "select.png")
    pygame.image.save(game.screen, out)
    print("saved:", out)


if __name__ == "__main__":
    main()

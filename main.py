# エントリポイント
# 通常起動:       python main.py
# 動作確認モード: python main.py --smoke  (約5秒で自動終了)

import sys

from game.game import Game


def main() -> None:
    smoke_frames = 300 if "--smoke" in sys.argv else 0
    Game(smoke_frames=smoke_frames).run()


if __name__ == "__main__":
    main()

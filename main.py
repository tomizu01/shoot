# エントリポイント
# 通常起動:       python main.py
# 動作確認モード: python main.py --smoke [フレーム数]  (デフォルト300=約5秒で自動終了)

import sys

from game.game import Game


def main() -> None:
    smoke_frames = 0
    if "--smoke" in sys.argv:
        idx = sys.argv.index("--smoke")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
            smoke_frames = int(sys.argv[idx + 1])
        else:
            smoke_frames = 300
    Game(smoke_frames=smoke_frames).run()


if __name__ == "__main__":
    main()

# 初期実装3(ステージCSV駆動)のロジック確認(ヘッドレス実行可)
# 実行: python tests/test_phase3.py

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game import config, stage  # noqa: E402
from game.entities import BigBoss, Enemy, MidBoss, PanelAdd, PanelMul, ItemBox  # noqa: E402
from game.game import (  # noqa: E402
    Game,
    STATE_ALL_CLEAR,
    STATE_PLAYING,
    STATE_STAGE_CLEAR,
    STATE_STAGE_SELECT,
)


def main():
    # --- CSV読み込み(Shift-JIS/UTF-8両対応、ヘッダー無視) ---
    events = stage.load_events(1)
    assert len(events) == 31, len(events)
    assert events[0] == (0, 1, "e1", 10), events[0]
    assert events[-1] == (6600, 2, "e3", 1000), events[-1]
    print("OK: stage1.csv 読み込み(31イベント)")

    # --- イベント→エンティティ生成 ---
    mgr = stage.StageManager(1)
    zako = mgr._build(0, 1, "e1", 10)
    assert len(zako) == 10 and all(isinstance(e, Enemy) for e in zako)
    # レーン1 → u=-0.75±ばらつき、奥行きは隊列でずれる
    assert all(abs(e.u - config.LANE_U[1]) <= config.ZAKO_CLUSTER_JITTER_U for e in zako)
    assert zako[-1].d > zako[0].d
    (mid,) = mgr._build(0, 2, "e2", 300)
    assert isinstance(mid, MidBoss) and mid.hp == 300 and mid.label() == "300"
    (big,) = mgr._build(0, 3, "e3", 1000)
    assert isinstance(big, BigBoss) and big.hp == 1000
    # 大ボスは2レーン占有: レーン2指定→2〜3の中間(u=0)、レーン4指定→3〜4の中間(u=0.5)
    assert mgr._build(0, 2, "e3", 1)[0].u == 0.0
    assert mgr._build(0, 3, "e3", 1)[0].u == 0.5
    assert mgr._build(0, 4, "e3", 1)[0].u == 0.5
    (p1,) = mgr._build(0, 3, "p1", 5)
    assert isinstance(p1, PanelAdd) and p1.n == 5 and p1.u == config.LANE_U[3]
    (p2,) = mgr._build(0, 4, "p2", 3)
    assert isinstance(p2, PanelMul) and p2.n == 3
    (p3,) = mgr._build(0, 1, "p3", 100)
    assert isinstance(p3, ItemBox) and p3.hp == 100
    print("OK: 全種類のイベント生成")

    # --- 雑魚のばらつきが味方の移動範囲(±U_LIMIT)を超えない ---
    for lane in (1, 4):
        for _ in range(50):
            for e in mgr._build(0, lane, "e1", 20):
                assert abs(e.u) <= config.U_LIMIT, (lane, e.u)
    print("OK: 雑魚の横位置は±U_LIMIT内")

    # --- 進行に応じた出現 ---
    mgr = stage.StageManager(1)
    spawned = mgr.update(dt_ms=1)  # 進行0.1: タイミング0の3イベント発生
    assert len(spawned) == 10 + 1 + 1, len(spawned)  # e1x10 + p1 + p1
    spawned = mgr.update(dt_ms=2990)  # 進行299: まだ300に届かない
    assert spawned == [], spawned
    spawned = mgr.update(dt_ms=20)  # 進行301: タイミング300のe1x10
    assert len(spawned) == 10, len(spawned)
    print("OK: 進行距離100/秒で順次出現")

    # --- クリア判定(最終6600+猶予300) ---
    mgr = stage.StageManager(1)
    mgr.update(dt_ms=68_990)  # 進行6899
    assert mgr.all_spawned() and not mgr.reached_end()
    mgr.update(dt_ms=20)      # 進行6901
    assert mgr.reached_end()
    print("OK: クリア判定の進行距離")

    # --- ステージ遷移: 攻撃力リセット、味方人数持ち越し ---
    game = Game()
    game.squad.set_count(50)
    game.squad.attack_power = 9
    game.start_stage(1)
    assert game.squad.count == 50 and game.squad.attack_power == 1
    print("OK: ステージ開始で攻撃力リセット・人数持ち越し")

    # --- ステージクリア → 次ステージへ ---
    game.start_stage(1)
    game.state = STATE_STAGE_CLEAR
    game.update_stage_clear(dt_ms=config.STAGE_CLEAR_WAIT_MS + 1)
    assert game.state == STATE_PLAYING and game.stage.number == 2
    print("OK: ステージ1クリアでステージ2へ")

    # --- 全クリア: 最終ステージの次が無ければ ALL_CLEAR ---
    last = stage.list_stages()[-1]
    game.start_stage(last)
    game.state = STATE_STAGE_CLEAR
    game.update_stage_clear(dt_ms=config.STAGE_CLEAR_WAIT_MS + 1)
    assert game.state == STATE_ALL_CLEAR, game.state
    print("OK: 最終ステージクリアでALL CLEAR")

    # --- ステージ選択画面 ---
    assert stage.list_stages() == list(range(1, 11)), stage.list_stages()
    game2 = Game()  # 通常起動(smoke指定なし)は選択画面から
    assert game2.state == STATE_STAGE_SELECT
    assert len(game2.select_buttons) == 10
    # ボタンクリック相当: ステージ3で新規開始(人数・スコア初期化)
    game2.squad.set_count(500)
    game2.score = 99
    game2.start_run(3)
    assert game2.state == STATE_PLAYING and game2.stage.number == 3
    assert game2.squad.count == 1 and game2.score == 0
    print("OK: ステージ選択画面(10ステージ・新規開始で初期化)")

    print("\n全テスト成功")


if __name__ == "__main__":
    main()

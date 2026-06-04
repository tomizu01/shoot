# 初期実装2のロジック確認(ヘッドレス実行可)
# 実行: python tests/test_phase2.py

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game.game import Game  # noqa: E402
from game.entities import Bullet, ItemBox, PanelAdd, PanelMul  # noqa: E402


def main():
    game = Game()

    # --- 部隊分解: 235人 → 100x2 + 10x3 + 1x5 ---
    game.squad.set_count(235)
    sizes = sorted(unit.size for unit in game.squad.units)
    assert sizes == [1] * 5 + [10] * 3 + [100] * 2, sizes
    print("OK: 部隊分解 235 ->", sizes)

    # --- 上限1000 ---
    game.squad.set_count(5000)
    assert game.squad.count == 1000
    print("OK: 上限1000")

    # --- 部隊の幅が画面横幅の1/4以内に収まる ---
    from game import config, projection
    half_corridor = projection.corridor_width(config.PLAYER_DEPTH) / 2
    for n in (9, 99, 999, 1000):
        game.squad.set_count(n)
        offsets_px = [u.u_offset * half_corridor for u in game.squad.units]
        span = max(offsets_px) - min(offsets_px)
        limit = config.SCREEN_WIDTH * config.SQUAD_MAX_WIDTH_RATIO
        assert span <= limit + 1, (n, span, limit)
    print("OK: 部隊幅は画面の1/4以内")

    # --- 隊列は左右対称で、左に寄せれば左端ユニットがU_LIMITまで届く ---
    for n in (2, 4, 7, 30):
        game.squad.set_count(n)
        offsets = [u.u_offset for u in game.squad.units]
        assert abs(max(offsets) + min(offsets)) < 1e-6, (n, offsets)
        # 部隊中心を左端まで寄せたとき、左端ユニットは±U_LIMITの端に到達できる
        leftmost = -game.squad.center_limit + min(offsets)
        assert abs(leftmost - (-config.U_LIMIT)) < 1e-6, (n, leftmost)
    print("OK: 隊列は左右対称・端まで届く")

    # --- +n パネル取得 ---
    game.start_run(1)
    panel = PanelAdd(u=game.squad.center_u)
    panel.d = game.squad.d
    panel.n = 7
    game.items = [panel]
    game.resolve_item_pickups()
    assert game.squad.count == 8, game.squad.count
    assert not panel.alive
    print("OK: +7 パネルで 1 -> 8")

    # --- ×n パネル取得 ---
    mul = PanelMul(u=game.squad.center_u)
    mul.d = game.squad.d
    mul.n = 3
    game.items = [mul]
    game.resolve_item_pickups()
    assert game.squad.count == 24, game.squad.count
    print("OK: x3 パネルで 8 -> 24")

    # --- 未破壊ボックス接触で半減 ---
    game.squad.set_count(100)
    box = ItemBox(u=game.squad.center_u)
    box.d = game.squad.d
    game.items = [box]
    game.resolve_item_pickups()
    assert game.squad.count == 50, game.squad.count
    print("OK: ボックス接触で 100 -> 50")

    # --- ボックスを弾で破壊して攻撃力+1 ---
    game.start_run(1)
    box = ItemBox(u=0.0)
    box.d = 0.5
    box.hp = 5
    bullet = Bullet(u=0.0, d=0.5, damage=100)
    game.items = [box]
    game.bullets = [bullet]
    game.enemies = []
    game.resolve_bullet_hits()
    assert not box.alive
    assert game.squad.attack_power == 2, game.squad.attack_power
    print("OK: ボックス破壊で攻撃力 1 -> 2")

    # --- 弾はパネルを素通りする ---
    panel = PanelAdd(u=0.0)
    panel.d = 0.5
    bullet = Bullet(u=0.0, d=0.5)
    game.items = [panel]
    game.bullets = [bullet]
    game.resolve_bullet_hits()
    assert panel.alive and bullet.alive
    print("OK: 弾はパネルを素通り")

    print("\n全テスト成功")


if __name__ == "__main__":
    main()

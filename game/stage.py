# ステージCSVの読み込みと進行管理
# CSVの仕様は docs/stage.md を参照
#   カラム: 登場タイミング(進行距離), レーン(1〜4), 種類(e1/e2/e3/p1/p2/p3), 数量
#   数量の意味は種類による(e1=体数, e2/e3=耐久, p1=+n, p2=×n, p3=耐久)

import csv
import os
import random
import re

from . import config
from .entities import BigBoss, Enemy, Entity, ItemBox, MidBoss, PanelAdd, PanelMul

STAGE_DIR = os.path.join(os.path.dirname(__file__), "..", config.STAGE_DIR)

KINDS = ("e1", "e2", "e3", "p1", "p2", "p3")


class StageError(Exception):
    """ステージCSVの形式エラー"""


def stage_path(number: int) -> str:
    return os.path.join(STAGE_DIR, f"stage{number}.csv")


def stage_exists(number: int) -> bool:
    return os.path.isfile(stage_path(number))


def list_stages() -> list[int]:
    """stagesフォルダに存在するステージ番号一覧(昇順)"""
    numbers = []
    for name in os.listdir(STAGE_DIR):
        m = re.fullmatch(r"stage(\d+)\.csv", name)
        if m:
            numbers.append(int(m.group(1)))
    return sorted(numbers)


def load_events(number: int) -> list[tuple[int, int, str, int]]:
    """ステージCSVを読み込む。戻り値: [(登場タイミング, レーン, 種類, 数量), ...]

    UTF-8(BOM付き含む)とShift-JISの両方を受け付ける。
    最初の1行はヘッダーとして無視。5カラム目以降も無視。
    """
    path = stage_path(number)
    try:
        text = open(path, encoding="utf-8-sig").read()
    except UnicodeDecodeError:
        text = open(path, encoding="cp932").read()

    events = []
    rows = list(csv.reader(text.splitlines()))
    for line_no, row in enumerate(rows[1:], start=2):  # ヘッダーを飛ばす
        if not row or not "".join(row).strip():
            continue
        try:
            timing, lane, kind, value = int(row[0]), int(row[1]), row[2].strip(), int(row[3])
        except (ValueError, IndexError):
            raise StageError(f"{path} {line_no}行目: 形式が不正です: {row}")
        if lane not in config.LANE_U:
            raise StageError(f"{path} {line_no}行目: レーンは1〜4です: {row}")
        if kind not in KINDS:
            raise StageError(f"{path} {line_no}行目: 種類が不正です: {row}")
        events.append((timing, lane, kind, value))
    return events


class StageManager:
    """進行距離に応じてステージCSVのイベントを発生させる"""

    def __init__(self, number: int):
        self.number = number
        self.events = load_events(number)
        self.index = 0
        self.progress = 0.0
        last_timing = self.events[-1][0] if self.events else 0
        self.end_progress = last_timing + config.STAGE_CLEAR_BUFFER

    def update(self, dt_ms: float) -> list[Entity]:
        """進行を進め、タイミングが来たイベントのエンティティを返す"""
        self.progress += config.STAGE_PROGRESS_PER_SEC * dt_ms / 1000
        spawned: list[Entity] = []
        while self.index < len(self.events) and self.events[self.index][0] <= self.progress:
            spawned.extend(self._build(*self.events[self.index]))
            self.index += 1
        return spawned

    def all_spawned(self) -> bool:
        return self.index >= len(self.events)

    def reached_end(self) -> bool:
        """最終イベント+猶予分まで進行したか(クリア判定は敵全滅も必要)"""
        return self.all_spawned() and self.progress >= self.end_progress

    def _build(self, timing: int, lane: int, kind: str, value: int) -> list[Entity]:
        u = config.LANE_U[lane]
        if kind == "e1":
            # 雑魚n体: レーン内で横にばらし、奥行きをずらして隊列で出す
            count = max(1, min(20, value))
            jitter = config.ZAKO_CLUSTER_JITTER_U
            # ばらつきが味方の横移動範囲(±U_LIMIT)を超えると倒せない敵になるためclamp
            return [
                Enemy(
                    u=max(-config.U_LIMIT, min(
                        config.U_LIMIT, u + random.uniform(-jitter, jitter)
                    )),
                    d=1.0 + i * config.ZAKO_CLUSTER_STEP_D,
                )
                for i in range(count)
            ]
        if kind == "e2":
            return [MidBoss(u, hp=value)]
        if kind == "e3":
            # 大ボスは2レーン分を占有: 指定レーンと右隣レーンの中間に出現
            # (レーン4指定時は右隣が無いのでレーン3〜4にまたがる)
            left_lane = min(lane, 3)
            u = (config.LANE_U[left_lane] + config.LANE_U[left_lane + 1]) / 2
            return [BigBoss(u, hp=value)]
        if kind == "p1":
            return [PanelAdd(u, n=value)]
        if kind == "p2":
            return [PanelMul(u, n=value)]
        if kind == "p3":
            return [ItemBox(u, hp=value)]
        raise StageError(f"未知の種類: {kind}")

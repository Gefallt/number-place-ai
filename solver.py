"""ナンプレの探索アルゴリズム(ビットマスク + 制約伝播)。

セルの候補を9bitの整数(ビットマスク)で管理し、盤面は複製せずに
in-placeで書き換えてバックトラックする(戻すときはBoard.unassign /
Board.restoreでundoする)。1回の呼び出しの中で、次の順に手が
尽きるまで繰り返してから分岐することで、探索木そのものを小さくしている。

1. naked single・hidden single(候補が1つしかないマス)を確定させる
2. それでも決まらなければ、naked pair・pointing pair(techniques.py)で
   候補を減らす
3. それでも決まらなければ、候補最小のマスで1つずつ仮置きして再帰する
"""

from collections import defaultdict, namedtuple

import reporting
import techniques
from board import BOARD_SIZE, POPCOUNT, box_index, iter_values

ScanResult = namedtuple(
    "ScanResult",
    [
        "contradiction",
        "empties",
        "row_candidates",
        "col_candidates",
        "box_candidates",
        "row_cells",
        "col_cells",
        "box_cells",
    ],
)

_CONTRADICTION = ScanResult(True, [], None, None, None, None, None, None)


def solve(board):
    """ナンプレを解く。見つかった解はすべて reporting 経由で出力する

    呼び出し前後で board の状態は変化しない(この呼び出しで行った
    assign・eliminateはすべて取り消して返る)。

    Args:
        board (board.Board): 盤面
    """
    reporting.solve_count += 1
    changes = []

    while True:
        scan = _scan(board)

        if scan.contradiction:
            _undo(board, changes)
            reporting.invalid_count += 1
            return

        if not scan.empties:
            reporting.output_answer(board.to_numpy())
            _undo(board, changes)
            return

        forced = _collect_forced_cells(scan)
        if forced is None:
            _undo(board, changes)
            reporting.invalid_count += 1
            return
        if forced:
            for (row, col), value in forced.items():
                board.assign(row, col, value)
                changes.append(("assign", row, col, value))
            continue

        if techniques.reduce_candidates(board, scan, changes):
            continue

        break

    # 確定処理・候補の絞り込みだけでは埋まらなかったので、
    # 候補が最小のマスで1つずつ試す
    row, col, mask, _ = min(scan.empties, key=lambda cell: cell[3])
    for value in iter_values(mask):
        board.assign(row, col, value)
        solve(board)
        board.unassign(row, col, value)

    _undo(board, changes)


def _undo(board, changes):
    for change in reversed(changes):
        kind, row, col, payload = change
        if kind == "assign":
            board.unassign(row, col, payload)
        else:
            board.restore(row, col, payload)


def _scan(board):
    """空きマスの候補と、行・列・エリアごとに「その数字が置けるマス」を集計する

    まだ置かれていない数字なのに置けるマスが1つもないユニットがあれば、
    その時点で矛盾として検出する。
    """
    empties = []
    row_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    col_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    box_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    row_cells = [[] for _ in range(BOARD_SIZE)]
    col_cells = [[] for _ in range(BOARD_SIZE)]
    box_cells = [[] for _ in range(BOARD_SIZE)]

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board.cells[row * BOARD_SIZE + col] != 0:
                continue
            mask = board.candidate_mask(row, col)
            if mask == 0:
                return _CONTRADICTION
            count = POPCOUNT[mask]
            cell = (row, col, mask, count)
            empties.append(cell)
            box = box_index(row, col)
            row_cells[row].append(cell)
            col_cells[col].append(cell)
            box_cells[box].append(cell)
            for value in iter_values(mask):
                row_candidates[row][value].append(col)
                col_candidates[col][value].append(row)
                box_candidates[box][value].append((row, col))

    if _has_unplaceable_value(board.row_masks, row_candidates):
        return _CONTRADICTION
    if _has_unplaceable_value(board.col_masks, col_candidates):
        return _CONTRADICTION
    if _has_unplaceable_value(board.box_masks, box_candidates):
        return _CONTRADICTION

    return ScanResult(
        False,
        empties,
        row_candidates,
        col_candidates,
        box_candidates,
        row_cells,
        col_cells,
        box_cells,
    )


def _has_unplaceable_value(unit_masks, unit_candidates):
    """まだ置かれていない数字なのに、置けるマスがないユニットがあるかを調べる"""
    for unit_mask, candidates in zip(unit_masks, unit_candidates):
        for value in iter_values(unit_mask):
            if not candidates.get(value):
                return True
    return False


def _collect_forced_cells(scan):
    """naked single・hidden singleで確定するマスを集める

    Returns:
        dict または None: {(row, col): value} の辞書。
        異なる確定処理が同じマスに違う値を要求した場合(矛盾)はNoneを返す
    """
    forced = {}

    def stage(row, col, value):
        key = (row, col)
        if key in forced and forced[key] != value:
            return False
        forced[key] = value
        return True

    for row, col, mask, count in scan.empties:
        if count == 1:
            value = next(iter_values(mask))
            if not stage(row, col, value):
                return None

    for row in range(BOARD_SIZE):
        for value, cols in scan.row_candidates[row].items():
            if len(cols) == 1 and not stage(row, cols[0], value):
                return None
    for col in range(BOARD_SIZE):
        for value, rows in scan.col_candidates[col].items():
            if len(rows) == 1 and not stage(rows[0], col, value):
                return None
    for box in range(BOARD_SIZE):
        for value, cells in scan.box_candidates[box].items():
            if len(cells) == 1:
                row, col = cells[0]
                if not stage(row, col, value):
                    return None

    return forced

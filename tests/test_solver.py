import pytest

import reporting
import solver
from board import BOARD_SIZE, Board

EASY_PUZZLE = (
    "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
)
SOLVED_EASY = (
    "534678912672195348198342567859761423426853791713924856961537284287419635345286179"
)
CONTRADICTORY_PUZZLE = "11" + "0" * 79  # 同じ行に1が2つ


@pytest.fixture(autouse=True)
def reset_reporting():
    reporting.reset()
    yield


def _solve(puzzle_string):
    board = Board([int(c) for c in puzzle_string])
    solver.solve(board)
    return board


def test_solve_already_solved_board_reports_one_answer():
    board = _solve(SOLVED_EASY)
    assert reporting.answer_count == 1
    assert reporting.invalid_count == 0
    assert board.cells == [int(c) for c in SOLVED_EASY]


def test_solve_easy_puzzle_finds_unique_answer():
    _solve(EASY_PUZZLE)
    assert reporting.answer_count == 1
    assert "".join(str(v) for row in reporting.answers[0] for v in row) == SOLVED_EASY


def test_solve_contradictory_puzzle_reports_no_answer():
    _solve(CONTRADICTORY_PUZZLE)
    assert reporting.answer_count == 0
    assert reporting.invalid_count > 0


def test_solve_restores_board_state_after_returning():
    cells = [int(c) for c in EASY_PUZZLE]
    board = Board(list(cells))
    row_masks_before = list(board.row_masks)
    col_masks_before = list(board.col_masks)
    box_masks_before = list(board.box_masks)
    eliminated_before = list(board.eliminated)

    solver.solve(board)

    assert board.cells == cells
    assert board.row_masks == row_masks_before
    assert board.col_masks == col_masks_before
    assert board.box_masks == box_masks_before
    assert board.eliminated == eliminated_before


def test_solve_finds_all_solutions_for_ambiguous_puzzle():
    # (row3,col5)<->(row4,col5), (row3,col8)<->(row4,col8) の値を入れ替えても
    # 成立する「deadly rectangle」を仕込んだ、解が2つある問題
    solved = [int(c) for c in SOLVED_EASY]
    for idx in (3 * 9 + 5, 3 * 9 + 8, 4 * 9 + 5, 4 * 9 + 8):
        solved[idx] = 0
    board = Board(solved)

    solver.solve(board)

    assert reporting.answer_count == 2


def test_undo_reverts_assign_and_eliminate_changes():
    board = Board([0] * (BOARD_SIZE * BOARD_SIZE))
    changes = [
        ("assign", 0, 0, 5),
        ("eliminate", 1, 1, 1 << 0),
    ]
    board.assign(0, 0, 5)
    board.eliminate(1, 1, 1 << 0, [])

    solver._undo(board, changes)

    assert board.cells[0] == 0
    assert board.eliminated[1 * BOARD_SIZE + 1] == 0


def test_scan_detects_zero_candidate_cell_as_contradiction():
    board = Board([0] * (BOARD_SIZE * BOARD_SIZE))
    board.eliminate(0, 0, (1 << BOARD_SIZE) - 1, [])  # (0,0)の候補を全滅させる

    scan = solver._scan(board)

    assert scan.contradiction is True


def test_scan_returns_candidates_for_partially_filled_board():
    cells = [int(c) for c in EASY_PUZZLE]
    board = Board(cells)

    scan = solver._scan(board)

    assert scan.contradiction is False
    empty_count = sum(1 for c in cells if c == 0)
    assert len(scan.empties) == empty_count


@pytest.mark.parametrize(
    "unit_masks, unit_candidates, expected",
    [
        ([0b1], [{}], True),  # 数字1が必要なのに置ける場所がない
        ([0b1], [{1: [0]}], False),  # 置ける場所がある
        ([0], [{}], False),  # そもそも必要な数字がない
    ],
)
def test_has_unplaceable_value(unit_masks, unit_candidates, expected):
    assert solver._has_unplaceable_value(unit_masks, unit_candidates) is expected


def test_scan_contradiction_when_row_has_unplaceable_value(monkeypatch):
    board = Board([0] * (BOARD_SIZE * BOARD_SIZE))
    monkeypatch.setattr(solver, "_has_unplaceable_value", lambda *_: True)

    scan = solver._scan(board)

    assert scan.contradiction is True


def test_scan_no_contradiction_when_all_units_placeable(monkeypatch):
    board = Board([0] * (BOARD_SIZE * BOARD_SIZE))
    monkeypatch.setattr(solver, "_has_unplaceable_value", lambda *_: False)

    scan = solver._scan(board)

    assert scan.contradiction is False


def _empty_defaultdicts():
    from collections import defaultdict

    return [defaultdict(list) for _ in range(BOARD_SIZE)]


def test_collect_forced_cells_naked_single():
    row_candidates = _empty_defaultdicts()
    col_candidates = _empty_defaultdicts()
    box_candidates = _empty_defaultdicts()
    scan = solver.ScanResult(
        contradiction=False,
        empties=[(0, 0, 1 << 4, 1)],  # 候補が5だけの1マス
        row_candidates=row_candidates,
        col_candidates=col_candidates,
        box_candidates=box_candidates,
        row_cells=[[] for _ in range(BOARD_SIZE)],
        col_cells=[[] for _ in range(BOARD_SIZE)],
        box_cells=[[] for _ in range(BOARD_SIZE)],
    )

    forced = solver._collect_forced_cells(scan)

    assert forced == {(0, 0): 5}


def test_collect_forced_cells_hidden_single_per_unit():
    row_candidates = _empty_defaultdicts()
    col_candidates = _empty_defaultdicts()
    box_candidates = _empty_defaultdicts()
    row_candidates[0][3] = [2]  # 行0では数字3は列2にしか置けない
    col_candidates[4][7] = [1]  # 列4では数字7は行1にしか置けない
    box_candidates[8][9 - 2] = [(8, 8)]  # ボックス8では数字7は(8,8)にしか置けない
    scan = solver.ScanResult(
        contradiction=False,
        empties=[(0, 2, 0b11, 2), (1, 4, 0b1000000, 1)],
        row_candidates=row_candidates,
        col_candidates=col_candidates,
        box_candidates=box_candidates,
        row_cells=[[] for _ in range(BOARD_SIZE)],
        col_cells=[[] for _ in range(BOARD_SIZE)],
        box_cells=[[] for _ in range(BOARD_SIZE)],
    )

    forced = solver._collect_forced_cells(scan)

    assert forced[(0, 2)] == 3
    assert forced[(1, 4)] == 7
    assert forced[(8, 8)] == 7


def test_collect_forced_cells_returns_none_on_conflict():
    row_candidates = _empty_defaultdicts()
    col_candidates = _empty_defaultdicts()
    box_candidates = _empty_defaultdicts()
    row_candidates[0][1] = [0]  # 行の確定処理は(0,0)=1を要求
    col_candidates[0][2] = [0]  # 列の確定処理は(0,0)=2を要求(矛盾)
    scan = solver.ScanResult(
        contradiction=False,
        empties=[(0, 0, 0b11, 2)],
        row_candidates=row_candidates,
        col_candidates=col_candidates,
        box_candidates=box_candidates,
        row_cells=[[] for _ in range(BOARD_SIZE)],
        col_cells=[[] for _ in range(BOARD_SIZE)],
        box_cells=[[] for _ in range(BOARD_SIZE)],
    )

    assert solver._collect_forced_cells(scan) is None


def test_solve_uses_naked_pair_reduction_branch(monkeypatch):
    """techniques.reduce_candidates が進捗あり/なしを返す両方の分岐を直接叩く

    naked/hidden singleでは決まらない(が候補は少なく、すぐ探索が終わる)
    盤面として、deadly rectangle入りの多解問題を使う。
    """
    calls = []

    def fake_reduce(board, scan, changes):
        calls.append(1)
        return len(calls) == 1  # 最初の1回だけ進捗ありとする

    monkeypatch.setattr(solver.techniques, "reduce_candidates", fake_reduce)

    solved = [int(c) for c in SOLVED_EASY]
    for idx in (3 * 9 + 5, 3 * 9 + 8, 4 * 9 + 5, 4 * 9 + 8):
        solved[idx] = 0
    board = Board(solved)

    solver.solve(board)

    assert len(calls) >= 2


def test_solve_treats_conflicting_forced_cells_as_contradiction(monkeypatch):
    """solve()の中で_collect_forced_cellsがNoneを返す経路を確認する"""
    monkeypatch.setattr(solver, "_collect_forced_cells", lambda scan: None)

    board = Board([int(c) for c in EASY_PUZZLE])
    solver.solve(board)

    assert reporting.answer_count == 0
    assert reporting.invalid_count == 1


def test_scan_contradiction_when_col_has_unplaceable_value(monkeypatch):
    calls = []

    def fake(*_args):
        calls.append(1)
        return len(calls) == 2  # 行はOK、列でNG

    board = Board([0] * (BOARD_SIZE * BOARD_SIZE))
    monkeypatch.setattr(solver, "_has_unplaceable_value", fake)

    scan = solver._scan(board)

    assert scan.contradiction is True
    assert len(calls) == 2


def test_scan_contradiction_when_box_has_unplaceable_value(monkeypatch):
    calls = []

    def fake(*_args):
        calls.append(1)
        return len(calls) == 3  # 行・列はOK、エリアでNG

    board = Board([0] * (BOARD_SIZE * BOARD_SIZE))
    monkeypatch.setattr(solver, "_has_unplaceable_value", fake)

    scan = solver._scan(board)

    assert scan.contradiction is True
    assert len(calls) == 3


def test_collect_forced_cells_conflict_within_naked_singles():
    """(理論上は起きないはずの)同じマスの重複エントリでも衝突を検出できる"""
    scan = solver.ScanResult(
        contradiction=False,
        empties=[(0, 0, 1 << 0, 1), (0, 0, 1 << 1, 1)],
        row_candidates=_empty_defaultdicts(),
        col_candidates=_empty_defaultdicts(),
        box_candidates=_empty_defaultdicts(),
        row_cells=[[] for _ in range(BOARD_SIZE)],
        col_cells=[[] for _ in range(BOARD_SIZE)],
        box_cells=[[] for _ in range(BOARD_SIZE)],
    )

    assert solver._collect_forced_cells(scan) is None


def test_collect_forced_cells_conflict_in_row_loop():
    row_candidates = _empty_defaultdicts()
    col_candidates = _empty_defaultdicts()
    box_candidates = _empty_defaultdicts()
    row_candidates[0][2] = [0]  # 行の確定処理は(0,0)=2を要求(矛盾)
    scan = solver.ScanResult(
        contradiction=False,
        empties=[(0, 0, 1 << 0, 1)],  # naked singleで(0,0)=1が先に確定済み
        row_candidates=row_candidates,
        col_candidates=col_candidates,
        box_candidates=box_candidates,
        row_cells=[[] for _ in range(BOARD_SIZE)],
        col_cells=[[] for _ in range(BOARD_SIZE)],
        box_cells=[[] for _ in range(BOARD_SIZE)],
    )

    assert solver._collect_forced_cells(scan) is None


def test_collect_forced_cells_conflict_in_box_loop():
    row_candidates = _empty_defaultdicts()
    col_candidates = _empty_defaultdicts()
    box_candidates = _empty_defaultdicts()
    box_candidates[0][2] = [(0, 0)]  # ボックス0の確定処理は(0,0)=2を要求(矛盾)
    scan = solver.ScanResult(
        contradiction=False,
        empties=[(0, 0, 1 << 0, 1)],  # naked singleで(0,0)=1が先に確定済み
        row_candidates=row_candidates,
        col_candidates=col_candidates,
        box_candidates=box_candidates,
        row_cells=[[] for _ in range(BOARD_SIZE)],
        col_cells=[[] for _ in range(BOARD_SIZE)],
        box_cells=[[] for _ in range(BOARD_SIZE)],
    )

    assert solver._collect_forced_cells(scan) is None

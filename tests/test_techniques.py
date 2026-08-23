from collections import defaultdict

import solver
import techniques
from board import BOARD_SIZE, Board


def _empty_board():
    return Board([0] * (BOARD_SIZE * BOARD_SIZE))


def _make_scan(**overrides):
    defaults = dict(
        contradiction=False,
        empties=[],
        row_candidates=[defaultdict(list) for _ in range(BOARD_SIZE)],
        col_candidates=[defaultdict(list) for _ in range(BOARD_SIZE)],
        box_candidates=[defaultdict(list) for _ in range(BOARD_SIZE)],
        row_cells=[[] for _ in range(BOARD_SIZE)],
        col_cells=[[] for _ in range(BOARD_SIZE)],
        box_cells=[[] for _ in range(BOARD_SIZE)],
    )
    defaults.update(overrides)
    return solver.ScanResult(**defaults)


# ---------------------------------------------------------------------------
# _apply_naked_pairs
# ---------------------------------------------------------------------------


def test_apply_naked_pairs_eliminates_from_other_cells():
    board = _empty_board()
    changes = []
    pair_mask = (1 << 0) | (1 << 1)  # 候補 {1, 2}
    unit_cells = [
        (0, 0, pair_mask, 2),
        (0, 1, pair_mask, 2),
        (0, 2, pair_mask | (1 << 2), 3),  # 候補 {1, 2, 3}
    ]

    progress = techniques._apply_naked_pairs(board, unit_cells, changes)

    assert progress is True
    assert board.eliminated[0 * BOARD_SIZE + 2] == pair_mask


def test_apply_naked_pairs_skips_cells_without_overlap():
    board = _empty_board()
    changes = []
    pair_mask = (1 << 0) | (1 << 1)
    unit_cells = [
        (0, 0, pair_mask, 2),
        (0, 1, pair_mask, 2),
        (0, 2, 1 << 2, 1),  # 候補{3}のみ、pairと被らない
    ]

    progress = techniques._apply_naked_pairs(board, unit_cells, changes)

    assert progress is False
    assert board.eliminated[0 * BOARD_SIZE + 2] == 0


def test_apply_naked_pairs_ignores_single_cell_with_pair_mask():
    board = _empty_board()
    changes = []
    pair_mask = (1 << 0) | (1 << 1)
    unit_cells = [
        (0, 0, pair_mask, 2),  # 同じ候補を持つ相方がいない
        (0, 1, pair_mask | (1 << 2), 3),
    ]

    progress = techniques._apply_naked_pairs(board, unit_cells, changes)

    assert progress is False


def test_apply_naked_pairs_ignores_cells_with_more_than_two_candidates():
    board = _empty_board()
    changes = []
    unit_cells = [
        (0, 0, (1 << 0) | (1 << 1) | (1 << 2), 3),
        (0, 1, (1 << 0) | (1 << 1) | (1 << 2), 3),
    ]

    progress = techniques._apply_naked_pairs(board, unit_cells, changes)

    assert progress is False


def test_apply_naked_pairs_returns_false_when_already_eliminated():
    board = _empty_board()
    pair_mask = (1 << 0) | (1 << 1)
    board.eliminate(0, 2, pair_mask, [])
    changes = []
    unit_cells = [
        (0, 0, pair_mask, 2),
        (0, 1, pair_mask, 2),
        (0, 2, pair_mask, 2),
    ]

    progress = techniques._apply_naked_pairs(board, unit_cells, changes)

    assert progress is False


# ---------------------------------------------------------------------------
# _apply_box_line_reduction (pointing pair)
# ---------------------------------------------------------------------------


def test_apply_box_line_reduction_skips_when_single_candidate_cell():
    board = _empty_board()
    changes = []
    scan = _make_scan(box_candidates=[defaultdict(list, {1: [(0, 0)]})] + [defaultdict(list) for _ in range(8)])

    progress = techniques._apply_box_line_reduction(board, 0, scan, changes)

    assert progress is False


def test_apply_box_line_reduction_eliminates_along_row():
    board = _empty_board()
    changes = []
    # box0内で数字1の候補が(0,0),(0,1)の2マス -> 行0の外側(box0以外)から1を除外
    box_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    box_candidates[0][1] = [(0, 0), (0, 1)]
    scan = _make_scan(box_candidates=box_candidates)

    progress = techniques._apply_box_line_reduction(board, 0, scan, changes)

    assert progress is True
    assert board.eliminated[0 * BOARD_SIZE + 5] & 1 == 1  # 行0・box0外のセルから1が消えた
    assert board.eliminated[0 * BOARD_SIZE + 0] == 0  # box内自身は変更されない


def test_apply_box_line_reduction_eliminates_along_column():
    board = _empty_board()
    changes = []
    # box0内で数字1の候補が(0,0),(1,0)の2マス -> 列0の外側(box0以外)から1を除外
    box_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    box_candidates[0][1] = [(0, 0), (1, 0)]
    scan = _make_scan(box_candidates=box_candidates)

    progress = techniques._apply_box_line_reduction(board, 0, scan, changes)

    assert progress is True
    assert board.eliminated[5 * BOARD_SIZE + 0] & 1 == 1  # 列0・box0外のセルから1が消えた


def test_apply_box_line_reduction_no_progress_when_spread_across_rows_and_cols():
    board = _empty_board()
    changes = []
    box_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    box_candidates[0][1] = [(0, 0), (0, 1), (1, 0)]  # 行も列も1つに収まらない
    scan = _make_scan(box_candidates=box_candidates)

    progress = techniques._apply_box_line_reduction(board, 0, scan, changes)

    assert progress is False


# ---------------------------------------------------------------------------
# _apply_line_box_reduction_row / _col
# ---------------------------------------------------------------------------


def test_apply_line_box_reduction_row_skips_when_single_candidate_cell():
    board = _empty_board()
    changes = []
    row_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    row_candidates[0][1] = [0]
    scan = _make_scan(row_candidates=row_candidates)

    progress = techniques._apply_line_box_reduction_row(board, 0, scan, changes)

    assert progress is False


def test_apply_line_box_reduction_row_eliminates_within_box():
    board = _empty_board()
    changes = []
    # 行0で数字1の候補が列0,1(=box0)だけ -> box0の行0以外のマスから1を除外
    row_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    row_candidates[0][1] = [0, 1]
    scan = _make_scan(row_candidates=row_candidates)

    progress = techniques._apply_line_box_reduction_row(board, 0, scan, changes)

    assert progress is True
    assert board.eliminated[1 * BOARD_SIZE + 0] & 1 == 1


def test_apply_line_box_reduction_row_no_progress_when_spans_multiple_boxes():
    board = _empty_board()
    changes = []
    row_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    row_candidates[0][1] = [0, 3]  # box0とbox1にまたがる
    scan = _make_scan(row_candidates=row_candidates)

    progress = techniques._apply_line_box_reduction_row(board, 0, scan, changes)

    assert progress is False


def test_apply_line_box_reduction_col_eliminates_within_box():
    board = _empty_board()
    changes = []
    col_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    col_candidates[0][1] = [0, 1]  # box0内に収まる
    scan = _make_scan(col_candidates=col_candidates)

    progress = techniques._apply_line_box_reduction_col(board, 0, scan, changes)

    assert progress is True
    assert board.eliminated[0 * BOARD_SIZE + 1] & 1 == 1


def test_apply_line_box_reduction_col_no_progress_when_spans_multiple_boxes():
    board = _empty_board()
    changes = []
    col_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    col_candidates[0][1] = [0, 3]
    scan = _make_scan(col_candidates=col_candidates)

    progress = techniques._apply_line_box_reduction_col(board, 0, scan, changes)

    assert progress is False


def test_apply_line_box_reduction_col_skips_when_single_candidate_cell():
    board = _empty_board()
    changes = []
    col_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    col_candidates[0][1] = [0]
    scan = _make_scan(col_candidates=col_candidates)

    progress = techniques._apply_line_box_reduction_col(board, 0, scan, changes)

    assert progress is False


# ---------------------------------------------------------------------------
# elimination helpers: box-range skip / filled-cell skip / already-eliminated
# ---------------------------------------------------------------------------


def test_eliminate_outside_box_in_row_skips_box_columns_and_filled_cells():
    board = _empty_board()
    board.assign(0, 4, 9)  # 行0・box1にある、box0の外の1マスを埋めておく
    changes = []
    bit = 1 << 0

    progress = techniques._eliminate_outside_box_in_row(board, 0, 0, bit, changes)

    assert progress is True
    assert board.eliminated[0 * BOARD_SIZE + 0] == 0  # box0内(自分自身)は対象外
    assert board.eliminated[0 * BOARD_SIZE + 4] == 0  # 埋まっているマスはスキップ
    assert board.eliminated[0 * BOARD_SIZE + 5] & bit == bit  # 空いていて対象範囲


def test_eliminate_outside_box_in_col_skips_box_rows_and_filled_cells():
    board = _empty_board()
    board.assign(4, 0, 9)
    changes = []
    bit = 1 << 0

    progress = techniques._eliminate_outside_box_in_col(board, 0, 0, bit, changes)

    assert progress is True
    assert board.eliminated[0 * BOARD_SIZE + 0] == 0
    assert board.eliminated[4 * BOARD_SIZE + 0] == 0
    assert board.eliminated[5 * BOARD_SIZE + 0] & bit == bit


def test_eliminate_outside_row_in_box_skips_source_row_and_filled_cells():
    board = _empty_board()
    board.assign(1, 1, 9)  # box0内、行0以外の1マスを埋めておく
    changes = []
    bit = 1 << 0

    progress = techniques._eliminate_outside_row_in_box(board, 0, 0, bit, changes)

    assert progress is True
    assert board.eliminated[0 * BOARD_SIZE + 1] == 0  # 元の行はスキップ
    assert board.eliminated[1 * BOARD_SIZE + 1] == 0  # 埋まっているマスはスキップ
    assert board.eliminated[2 * BOARD_SIZE + 0] & bit == bit


def test_eliminate_outside_col_in_box_skips_source_col_and_filled_cells():
    board = _empty_board()
    board.assign(1, 1, 9)
    changes = []
    bit = 1 << 0

    progress = techniques._eliminate_outside_col_in_box(board, 0, 0, bit, changes)

    assert progress is True
    assert board.eliminated[1 * BOARD_SIZE + 0] == 0  # 元の列はスキップ
    assert board.eliminated[1 * BOARD_SIZE + 1] == 0  # 埋まっているマスはスキップ
    assert board.eliminated[0 * BOARD_SIZE + 2] & bit == bit


def test_eliminate_outside_box_in_row_no_progress_when_already_eliminated():
    board = _empty_board()
    bit = 1 << 0
    for col in (3, 4, 5, 6, 7, 8):
        board.eliminate(0, col, bit, [])
    changes = []

    progress = techniques._eliminate_outside_box_in_row(board, 0, 0, bit, changes)

    assert progress is False


# ---------------------------------------------------------------------------
# reduce_candidates (統合)
# ---------------------------------------------------------------------------


def test_reduce_candidates_returns_true_via_naked_pair():
    board = _empty_board()
    changes = []
    pair_mask = (1 << 0) | (1 << 1)
    row_cells = [[] for _ in range(BOARD_SIZE)]
    row_cells[0] = [
        (0, 0, pair_mask, 2),
        (0, 1, pair_mask, 2),
        (0, 2, pair_mask | (1 << 2), 3),
    ]
    scan = _make_scan(row_cells=row_cells)

    progress = techniques.reduce_candidates(board, scan, changes)

    assert progress is True
    assert board.eliminated[0 * BOARD_SIZE + 2] == pair_mask


def test_reduce_candidates_falls_through_to_line_reductions_when_no_naked_pair():
    board = _empty_board()
    changes = []
    box_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    box_candidates[0][1] = [(0, 0), (0, 1)]
    scan = _make_scan(box_candidates=box_candidates)

    progress = techniques.reduce_candidates(board, scan, changes)

    assert progress is True
    assert board.eliminated[0 * BOARD_SIZE + 5] & 1 == 1


def test_reduce_candidates_returns_false_when_nothing_to_reduce():
    board = _empty_board()
    changes = []
    scan = _make_scan()

    progress = techniques.reduce_candidates(board, scan, changes)

    assert progress is False


def test_reduce_candidates_applies_line_box_reduction_row():
    board = _empty_board()
    changes = []
    row_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    row_candidates[0][1] = [0, 1]  # box0に収まる
    scan = _make_scan(row_candidates=row_candidates)

    progress = techniques.reduce_candidates(board, scan, changes)

    assert progress is True
    assert board.eliminated[1 * BOARD_SIZE + 0] & 1 == 1


def test_reduce_candidates_applies_line_box_reduction_col():
    board = _empty_board()
    changes = []
    col_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    col_candidates[0][1] = [0, 1]  # box0に収まる
    scan = _make_scan(col_candidates=col_candidates)

    progress = techniques.reduce_candidates(board, scan, changes)

    assert progress is True
    assert board.eliminated[0 * BOARD_SIZE + 1] & 1 == 1


def test_apply_box_line_reduction_row_branch_with_no_new_elimination():
    """行が1つに収まる(if len(rows)==1)がすでに全部除外済みでprogressがFalseのまま
    次のcols判定に進むケース
    """
    board = _empty_board()
    bit = 1 << 0
    for col in (3, 4, 5, 6, 7, 8):
        board.eliminate(0, col, bit, [])
    changes = []
    box_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    box_candidates[0][1] = [(0, 0), (0, 1)]  # rows={0} cols={0,1}
    scan = _make_scan(box_candidates=box_candidates)

    progress = techniques._apply_box_line_reduction(board, 0, scan, changes)

    assert progress is False


def test_apply_line_box_reduction_row_branch_with_no_new_elimination():
    board = _empty_board()
    bit = 1 << 0
    board.eliminate(1, 0, bit, [])
    board.eliminate(1, 1, bit, [])
    board.eliminate(1, 2, bit, [])
    board.eliminate(2, 0, bit, [])
    board.eliminate(2, 1, bit, [])
    board.eliminate(2, 2, bit, [])
    changes = []
    row_candidates = [defaultdict(list) for _ in range(BOARD_SIZE)]
    row_candidates[0][1] = [0, 1]  # box0に収まる
    scan = _make_scan(row_candidates=row_candidates)

    progress = techniques._apply_line_box_reduction_row(board, 0, scan, changes)

    assert progress is False


def test_eliminate_outside_row_in_box_no_progress_when_already_eliminated():
    board = _empty_board()
    bit = 1 << 0
    # box0(行0-2, 列0-2)のうち、行0以外を全て除外済みにしておく
    for r, c in ((1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)):
        board.eliminate(r, c, bit, [])
    changes = []

    progress = techniques._eliminate_outside_row_in_box(board, 0, 0, bit, changes)

    assert progress is False


def test_eliminate_outside_col_in_box_no_progress_when_already_eliminated():
    board = _empty_board()
    bit = 1 << 0
    # box0(行0-2, 列0-2)のうち、列0以外を全て除外済みにしておく
    for r, c in ((0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)):
        board.eliminate(r, c, bit, [])
    changes = []

    progress = techniques._eliminate_outside_col_in_box(board, 0, 0, bit, changes)

    assert progress is False

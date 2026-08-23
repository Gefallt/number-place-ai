"""naked pair・pointing pair(box-line reduction)による候補の絞り込み。

naked/hidden singleだけではマスを確定できない盤面でも、これらの手法で
候補を減らせれば新たなsingleが生まれることがある。1回のsolve呼び出しの
中で、確定するマスがなくなった後・分岐する前にこれらを試す。
"""

from collections import defaultdict

from board import BLOCK_SIZE, BOARD_SIZE, box_index


def reduce_candidates(board, scan, changes):
    """naked pair・pointing pairを使って候補を減らす

    Args:
        board (board.Board): 盤面
        scan (solver.ScanResult): 直前のスキャン結果
        changes (list): このsolve呼び出し内での変更を記録するログ

    Returns:
        bool: 何か候補を減らせたらTrue(呼び出し側は再スキャンする)
    """
    progress = False
    for unit_cells in (*scan.row_cells, *scan.col_cells, *scan.box_cells):
        if _apply_naked_pairs(board, unit_cells, changes):
            progress = True
    if progress:
        # naked pairで候補が変わったなら、先にhidden singleを拾い直す
        return True

    for box in range(BOARD_SIZE):
        if _apply_box_line_reduction(board, box, scan, changes):
            progress = True
    for row in range(BOARD_SIZE):
        if _apply_line_box_reduction_row(board, row, scan, changes):
            progress = True
    for col in range(BOARD_SIZE):
        if _apply_line_box_reduction_col(board, col, scan, changes):
            progress = True
    return progress


def _apply_naked_pairs(board, unit_cells, changes):
    """同じユニット内で、候補が全く同じ2マスがあれば(naked pair)、
    そのユニットの他のマスからその2つの数字を除外する
    """
    progress = False
    cells_by_mask = defaultdict(list)
    for row, col, mask, count in unit_cells:
        if count == 2:
            cells_by_mask[mask].append((row, col))

    for mask, pair_cells in cells_by_mask.items():
        if len(pair_cells) < 2:
            continue
        pair_cell_set = set(pair_cells)
        for row, col, cell_mask, _count in unit_cells:
            if (row, col) in pair_cell_set:
                continue
            overlap = cell_mask & mask
            if overlap and board.eliminate(row, col, overlap, changes):
                progress = True
    return progress


def _apply_box_line_reduction(board, box, scan, changes):
    """エリア内で、ある数字の候補が1つの行(または列)に収まっているなら、
    その数字をエリア外の同じ行(列)から除外する(pointing pair)
    """
    progress = False
    for value, cells in scan.box_candidates[box].items():
        if len(cells) < 2:
            continue
        rows = {row for row, _col in cells}
        cols = {col for _row, col in cells}
        bit = 1 << (value - 1)
        if len(rows) == 1:
            row = next(iter(rows))
            if _eliminate_outside_box_in_row(board, row, box, bit, changes):
                progress = True
        if len(cols) == 1:
            col = next(iter(cols))
            if _eliminate_outside_box_in_col(board, col, box, bit, changes):
                progress = True
    return progress


def _apply_line_box_reduction_row(board, row, scan, changes):
    """行内で、ある数字の候補が1つのエリアに収まっているなら、
    その数字を行外の同じエリアから除外する
    """
    progress = False
    for value, cols in scan.row_candidates[row].items():
        if len(cols) < 2:
            continue
        boxes = {box_index(row, col) for col in cols}
        if len(boxes) == 1:
            bit = 1 << (value - 1)
            if _eliminate_outside_row_in_box(board, next(iter(boxes)), row, bit, changes):
                progress = True
    return progress


def _apply_line_box_reduction_col(board, col, scan, changes):
    """列内で、ある数字の候補が1つのエリアに収まっているなら、
    その数字を列外の同じエリアから除外する
    """
    progress = False
    for value, rows in scan.col_candidates[col].items():
        if len(rows) < 2:
            continue
        boxes = {box_index(row, col) for row in rows}
        if len(boxes) == 1:
            bit = 1 << (value - 1)
            if _eliminate_outside_col_in_box(board, next(iter(boxes)), col, bit, changes):
                progress = True
    return progress


def _box_bounds(box):
    row_start = (box // BLOCK_SIZE) * BLOCK_SIZE
    col_start = (box % BLOCK_SIZE) * BLOCK_SIZE
    return row_start, col_start


def _eliminate_outside_box_in_row(board, row, box, bit, changes):
    progress = False
    _row_start, col_start = _box_bounds(box)
    for col in range(BOARD_SIZE):
        if col_start <= col < col_start + BLOCK_SIZE:
            continue
        if board.cells[row * BOARD_SIZE + col] != 0:
            continue
        if board.eliminate(row, col, bit, changes):
            progress = True
    return progress


def _eliminate_outside_box_in_col(board, col, box, bit, changes):
    progress = False
    row_start, _col_start = _box_bounds(box)
    for row in range(BOARD_SIZE):
        if row_start <= row < row_start + BLOCK_SIZE:
            continue
        if board.cells[row * BOARD_SIZE + col] != 0:
            continue
        if board.eliminate(row, col, bit, changes):
            progress = True
    return progress


def _eliminate_outside_row_in_box(board, box, row, bit, changes):
    progress = False
    row_start, col_start = _box_bounds(box)
    for r in range(row_start, row_start + BLOCK_SIZE):
        if r == row:
            continue
        for c in range(col_start, col_start + BLOCK_SIZE):
            if board.cells[r * BOARD_SIZE + c] != 0:
                continue
            if board.eliminate(r, c, bit, changes):
                progress = True
    return progress


def _eliminate_outside_col_in_box(board, box, col, bit, changes):
    progress = False
    row_start, col_start = _box_bounds(box)
    for c in range(col_start, col_start + BLOCK_SIZE):
        if c == col:
            continue
        for r in range(row_start, row_start + BLOCK_SIZE):
            if board.cells[r * BOARD_SIZE + c] != 0:
                continue
            if board.eliminate(r, c, bit, changes):
                progress = True
    return progress

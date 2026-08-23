"""ナンプレの探索アルゴリズム。"""

from collections import defaultdict
from copy import deepcopy

import board as board_module
import reporting

BOARD_SIZE = board_module.BOARD_SIZE
BLOCK_SIZE = board_module.BLOCK_SIZE


def solve_number_place(board, column_candidates, row_candidates, area_candidates):
    """ナンプレを解く

    Args:
        board (numpy.ndarray): 数字のリスト
        column_candidates (list): 各列の候補となる数字の集合が入ったリスト
        row_candidates (list): 各行の候補となる数字の集合が入ったリスト
        area_candidates (list): 各エリアの候補となる数字の集合が入ったリスト
    """
    reporting.solve_count += 1
    # 各マスの候補となる数字の集合が入ったリストを取得
    cell_candidates = deepcopy(
        board_module.get_cell_candidates(
            board, column_candidates, row_candidates, area_candidates
        )
    )
    # まだ決定していない座標のリストを取得
    undecided_cells = get_least_candidate_cells(cell_candidates)

    # まだ決定していない座標がない場合、ナンプレが正しいかどうかを判定する
    if len(undecided_cells) == 0:
        if not board_module.is_valid_board(board):
            reporting.invalid_count += 1
            return
        reporting.output_answer(board)
        return

    # 候補が1つしかない座標のリストを取得
    forced_cells = get_forced_cells(cell_candidates)

    # 候補が1つしかない座標がある場合、その座標を埋めて再帰処理を行う
    if len(forced_cells) > 0:
        for value, col, row in forced_cells:
            board[row][col] = value
            column_candidates[col].discard(value)
            row_candidates[row].discard(value)
            area_candidates[row // BLOCK_SIZE][col // BLOCK_SIZE].discard(value)
        solve_number_place(
            deepcopy(board),
            deepcopy(column_candidates),
            deepcopy(row_candidates),
            deepcopy(area_candidates),
        )
        return

    # 候補が1つしかない座標がない場合、候補の中から1つ数字を選んで再帰処理を行う
    row = undecided_cells[0] // BOARD_SIZE
    col = undecided_cells[0] % BOARD_SIZE

    # 候補の中から1つ数字を選んで再帰処理を行う
    for value in cell_candidates[row][col]:
        board[row][col] = value
        new_column_candidates = deepcopy(column_candidates)
        new_column_candidates[col].discard(value)
        new_row_candidates = deepcopy(row_candidates)
        new_row_candidates[row].discard(value)
        new_area_candidates = deepcopy(area_candidates)
        new_area_candidates[row // BLOCK_SIZE][col // BLOCK_SIZE].discard(value)
        solve_number_place(
            deepcopy(board),
            deepcopy(new_column_candidates),
            deepcopy(new_row_candidates),
            deepcopy(new_area_candidates),
        )


def get_least_candidate_cells(cell_candidates):
    """各マスの候補となる数字の集合の数が最小となるマスの座標のリストを返す
    座標のリストは、行番号 * BOARD_SIZE + 列番号で表す

    Args:
        cell_candidates (list of list): 各マスの候補となる数字の集合が入ったリスト

    Returns:
        list: 各マスの候補となる数字の集合の数が最小となるマスの座標のリスト
    """
    cells_by_candidate_count = defaultdict(list)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            candidate_count = len(cell_candidates[row][col])
            if candidate_count == 0:
                continue
            cells_by_candidate_count[candidate_count].append(row * BOARD_SIZE + col)
    if not cells_by_candidate_count:
        return []
    return cells_by_candidate_count[min(cells_by_candidate_count.keys())]


def get_forced_cells(cell_candidates):
    """候補が1つしかない座標のリストを返却する

    Args:
        cell_candidates (list of list): 各マスの候補となる数字の集合が入ったリスト

    Returns:
        list: 候補が1つしかない座標の [数字, 列, 行] のリスト
    """
    forced_cells = []

    # そもそも1つしか入らない枠が既に確定しているのであれば入れてしまう
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if len(cell_candidates[row][col]) != 1:
                continue
            value = next(iter(cell_candidates[row][col]))
            cell = [value, col, row]
            if cell not in forced_cells:
                forced_cells.append(cell)

    # rowの中で一意に決まったものがあればそれを返す
    for row in range(BOARD_SIZE):
        for value in range(1, BOARD_SIZE + 1):
            found_col = -1
            for col in range(BOARD_SIZE):
                if value not in cell_candidates[row][col]:
                    continue
                if found_col >= 0:
                    found_col = -1
                    break
                found_col = col
            if found_col >= 0:
                cell = [value, found_col, row]
                if cell not in forced_cells:
                    forced_cells.append(cell)

    # colの中で一意に決まったものがあればそれを返す
    for col in range(BOARD_SIZE):
        for value in range(1, BOARD_SIZE + 1):
            found_row = -1
            for row in range(BOARD_SIZE):
                if value not in cell_candidates[row][col]:
                    continue
                if found_row >= 0:
                    found_row = -1
                    break
                found_row = row
            if found_row >= 0:
                cell = [value, col, found_row]
                if cell not in forced_cells:
                    forced_cells.append(cell)

    # areaの中で一意に決まったものがあればそれを返す
    for area_row_start in range(0, BOARD_SIZE, BLOCK_SIZE):
        for area_col_start in range(0, BOARD_SIZE, BLOCK_SIZE):
            for value in range(1, BOARD_SIZE + 1):
                found_offset = -1
                for offset in range(BOARD_SIZE):
                    row = area_row_start + offset // BLOCK_SIZE
                    col = area_col_start + offset % BLOCK_SIZE
                    if value not in cell_candidates[row][col]:
                        continue
                    if found_offset >= 0:
                        found_offset = -1
                        break
                    found_offset = offset
                if found_offset >= 0:
                    cell = [
                        value,
                        area_col_start + found_offset % BLOCK_SIZE,
                        area_row_start + found_offset // BLOCK_SIZE,
                    ]
                    if cell not in forced_cells:
                        forced_cells.append(cell)
    return forced_cells

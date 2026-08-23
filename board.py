"""ナンプレの盤面表現と候補計算。"""

import numpy as np

# 一辺のマス数
BOARD_SIZE = 9
# エリア（3x3ブロック）の一辺のマス数
BLOCK_SIZE = int(np.sqrt(BOARD_SIZE))
# 1〜BOARD_SIZEの数字の集合
ALL_NUMBERS = set(range(1, BOARD_SIZE + 1))


def parse_board(input_string):
    """81桁の数字文字列を9x9のnumpy配列に変換する

    Args:
        input_string (str): 81桁の数字文字列（0は空マス）

    Returns:
        numpy.ndarray: 9x9の盤面
    """
    return np.array(
        [
            [int(input_string[BOARD_SIZE * row + col]) for col in range(BOARD_SIZE)]
            for row in range(BOARD_SIZE)
        ]
    )


def get_column_candidates(board):
    """各列でまだ使われていない数字の集合のリストを返す

    Args:
        board (numpy.ndarray): 数字のリスト

    Returns:
        list: 各列の候補となる数字の集合が入ったリスト
    """
    return [ALL_NUMBERS - set(board[:, col]) for col in range(BOARD_SIZE)]


def get_row_candidates(board):
    """各行でまだ使われていない数字の集合のリストを返す

    Args:
        board (numpy.ndarray): 数字のリスト

    Returns:
        list: 各行の候補となる数字の集合が入ったリスト
    """
    return [ALL_NUMBERS - set(board[row, :]) for row in range(BOARD_SIZE)]


def get_area_candidates(board):
    """各エリア（3x3）でまだ使われていない数字の集合のリストを返す

    Args:
        board (numpy.ndarray): 数字のリスト

    Returns:
        list of list: 各エリアの候補となる数字の集合が入ったリスト
    """
    return [
        [
            ALL_NUMBERS
            - set(
                board[
                    block_row * BLOCK_SIZE : (block_row + 1) * BLOCK_SIZE,
                    block_col * BLOCK_SIZE : (block_col + 1) * BLOCK_SIZE,
                ].ravel()
            )
            for block_col in range(BLOCK_SIZE)
        ]
        for block_row in range(BLOCK_SIZE)
    ]


def get_cell_candidates(board, column_candidates, row_candidates, area_candidates):
    """各マスの候補となる数字の集合が入ったリストを返す

    Args:
        board (numpy.ndarray): 数字のリスト
        column_candidates (list): 各列の候補となる数字の集合が入ったリスト
        row_candidates (list): 各行の候補となる数字の集合が入ったリスト
        area_candidates (list): 各エリアの候補となる数字の集合が入ったリスト

    Returns:
        list of list: 各マスの候補となる数字の集合が入ったリスト
    """
    cell_candidates = [[set() for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] != 0:
                continue
            cell_candidates[row][col] = (
                area_candidates[row // BLOCK_SIZE][col // BLOCK_SIZE]
                & column_candidates[col]
                & row_candidates[row]
            )
    return cell_candidates


def is_valid_board(board):
    """盤面が数独のルールを満たしているかどうかを判定する

    Args:
        board (numpy.ndarray): 数字のリスト

    Returns:
        bool: 正しければTrue、正しくなければFalse
    """
    for candidates in get_column_candidates(board):
        if candidates:
            return False
    for candidates in get_row_candidates(board):
        if candidates:
            return False
    for row in get_area_candidates(board):
        for candidates in row:
            if candidates:
                return False
    return True

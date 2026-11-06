import json
import time
from copy import copy

from openpyxl import load_workbook
from openpyxl.formula.translate import Translator

INPUT_FILE = "sudoku_x_complete.xlsx"
OUTPUT_FILE = "sudoku_x_learning.xlsx"

WAIT_TIME = 0.015            # ## 0.015 ##

BRAIN_FILE = "brain_weights.json"


# --------------------------------------------------
# 脳読込
# --------------------------------------------------
def load_brain():

    try:

        with open(
            BRAIN_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except FileNotFoundError:

        return {
            "row_scores": [0] * 9
        }


# --------------------------------------------------
# 脳保存
# --------------------------------------------------
def save_brain(brain):

    with open(
        
        BRAIN_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            brain,
            f,
            indent=4
        )


brain = load_brain()


# --------------------------------------------------
# 妥当性
# --------------------------------------------------
def is_valid(board, row, col, num):

    for c in range(9):
        if board[row][c] == num:
            return False

    for r in range(9):
        if board[r][col] == num:
            return False

    br = (row // 3) * 3
    bc = (col // 3) * 3

    for r in range(br, br + 3):
        for c in range(bc, bc + 3):

            if board[r][c] == num:
                return False

    return True


# --------------------------------------------------
# 学習済み行順
# --------------------------------------------------
def get_row_priority():

    scores = brain["row_scores"]

    rows = list(range(9))

    rows.sort(
        key=lambda r: scores[r],
        reverse=True
    )

    return rows


# --------------------------------------------------
# 学習探索
# --------------------------------------------------
def find_empty_learning(board):

    row_order = get_row_priority()

    for r in row_order:

        for c in range(9):

            if board[r][c] == 0:
                return r, c

    return None


# --------------------------------------------------
# Solver
# --------------------------------------------------
def solve(board):

    pos = find_empty_learning(board)

    if pos is None:
        return True

    row, col = pos
# >>>    
    print(f"row={row} col={col}")
# <<<
    for num in range(1, 10):

        if is_valid(
            board,
            row,
            col,
            num
        ):

            board[row][col] = num

            brain["row_scores"][row] += 1

            time.sleep(
                WAIT_TIME
            )

            if solve(board):
                return True

            board[row][col] = 0

    return False


# --------------------------------------------------
# セルコピー
# --------------------------------------------------
def copy_cell(src, dst):

    if src.has_style:

        dst.font = copy(src.font)
        dst.fill = copy(src.fill)
        dst.border = copy(src.border)
        dst.alignment = copy(src.alignment)
        dst.number_format = copy(src.number_format)
        dst.protection = copy(src.protection)

    if (
        isinstance(src.value, str)
        and
        src.value.startswith("=")
    ):

        dst.value = Translator(
            src.value,
            origin=src.coordinate
        ).translate_formula(
            dst.coordinate
        )

    else:

        dst.value = src.value


# --------------------------------------------------
# Excel読込
# --------------------------------------------------
wb = load_workbook(
    INPUT_FILE
)

ws = wb.active


# --------------------------------------------------
# 問題取得
# --------------------------------------------------
board = []

for r in range(2, 11):

    row = []

    for c in range(2, 11):

        value = ws.cell(
            r,
            c
        ).value

        if value is None:
            value = 0

        row.append(
            int(value)
        )

    board.append(row)


# --------------------------------------------------
# solve
# --------------------------------------------------
start_time = (
    time.perf_counter()
)

if not solve(board):

    raise Exception(
        "解が存在しません"
    )

elapsed_ms = (
    time.perf_counter()
    - start_time
) * 1000


# --------------------------------------------------
# テンプレートコピー
# --------------------------------------------------
for r in range(1, 13):

    for c in range(1, 12):

        copy_cell(
            ws.cell(r, c),
            ws.cell(r + 12, c)
        )


# --------------------------------------------------
# 解答
# --------------------------------------------------
for r in range(9):

    for c in range(9):

        ws.cell(
            r + 14,
            c + 2
        ).value = board[r][c]


# --------------------------------------------------
# 統計
# --------------------------------------------------
ws["C24"] = round(
    elapsed_ms,
    0
)

ws["E24"] = "LEARNING"


# --------------------------------------------------
# 脳保存
# --------------------------------------------------
save_brain(brain)

# --------------------------------------------------
# 保存
# --------------------------------------------------
wb.save(
    OUTPUT_FILE
)

print()
print("Learning Solver")
print(
    f"time = {elapsed_ms:.0f} ms"
)

print(
    brain["row_scores"]
)

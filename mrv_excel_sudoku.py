import time
from copy import copy

from openpyxl import load_workbook
from openpyxl.formula.translate import Translator


INPUT_FILE = "sudoku_x_complete.xlsx"
OUTPUT_FILE = "sudoku_x_completed_mrv.xlsx"

# ------------------------------------------
# 思考時間(秒)
# ------------------------------------------
WAIT_TIME = 0.015


# --------------------------------------------------
# 妥当性チェック
# --------------------------------------------------
def is_valid(board, row, col, num):

    # 行
    for c in range(9):
        if board[row][c] == num:
            return False

    # 列
    for r in range(9):
        if board[r][col] == num:
            return False

    # ブロック
    br = (row // 3) * 3
    bc = (col // 3) * 3

    for r in range(br, br + 3):
        for c in range(bc, bc + 3):

            if board[r][c] == num:
                return False

    return True


# --------------------------------------------------
# 候補取得
# --------------------------------------------------
def get_candidates(board, row, col):

    candidates = []

    for num in range(1, 10):

        if is_valid(board, row, col, num):
            candidates.append(num)

    return candidates


# --------------------------------------------------
# MRV
# 候補数最少セルを選択
# --------------------------------------------------
def find_empty_mrv(board):

    best_pos = None
    best_candidate_count = 10

    for r in range(9):

        for c in range(9):

            if board[r][c] != 0:
                continue

            count = len(
                get_candidates(board, r, c)
            )

            if count < best_candidate_count:

                best_candidate_count = count
                best_pos = (r, c)

                # 最強条件
                if count == 1:
                    return best_pos

    return best_pos


# --------------------------------------------------
# Solver(MRV)
# --------------------------------------------------
def solve(board):

    pos = find_empty_mrv(board)

    if pos is None:
        return True

    row, col = pos

    candidates = get_candidates(
        board,
        row,
        col
    )

    for num in candidates:

        board[row][col] = num

        # 思考演出
        time.sleep(WAIT_TIME)

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
wb = load_workbook(INPUT_FILE)

ws = wb.active


# --------------------------------------------------
# 問題取得
# B2:J10
# --------------------------------------------------
board = []

for r in range(2, 11):

    row = []

    for c in range(2, 11):

        value = ws.cell(r, c).value

        if value is None:
            value = 0

        row.append(int(value))

    board.append(row)


# --------------------------------------------------
# 解く
# --------------------------------------------------
start_time = time.perf_counter()

if not solve(board):
    raise Exception("解が存在しません")

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
# 解答出力
# B14:J22
# --------------------------------------------------
for r in range(9):

    for c in range(9):

        ws.cell(
            row=r + 14,
            column=c + 2
        ).value = board[r][c]


# --------------------------------------------------
# 時間出力
# C24
# --------------------------------------------------
ws["C24"] = round(
    elapsed_ms,
    0
)

# MRV識別
ws["E24"] = "MRV"


# --------------------------------------------------
# 保存
# --------------------------------------------------
wb.save(OUTPUT_FILE)

print()
print("MRV Solver")
print(OUTPUT_FILE)
print(
    f"elapsed_time = {elapsed_ms:.0f} ms"
)

print()

for row in board:
    print(row)
import time
from copy import copy

from openpyxl import load_workbook
from openpyxl.formula.translate import Translator


INPUT_FILE = "sudoku_x_complete.xlsx"
OUTPUT_FILE = "sudoku_x_completed.xlsx"

# ------------------------------------------
# 思考時間(秒)
# 調整用
# ------------------------------------------
WAIT_TIME = 0.015


# --------------------------------------------------
# 数独判定（通常版）
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
# 空セル検索
# --------------------------------------------------
def find_empty(board):

    for r in range(9):
        for c in range(9):

            if board[r][c] == 0:
                return r, c

    return None


# --------------------------------------------------
# Solver
# --------------------------------------------------
def solve(board):

    pos = find_empty(board)

    if pos is None:
        return True

    row, col = pos

    for num in range(1, 10):

        if is_valid(board, row, col, num):

            board[row][col] = num

            # 思考中を演出
            time.sleep(WAIT_TIME)

            if solve(board):
                return True

            board[row][col] = 0

    return False


# --------------------------------------------------
# セルコピー
# Excelと同じ相対コピー
# --------------------------------------------------
def copy_cell(src, dst):

    if src.has_style:

        dst.font = copy(src.font)
        dst.fill = copy(src.fill)
        dst.border = copy(src.border)
        dst.alignment = copy(src.alignment)
        dst.number_format = copy(src.number_format)
        dst.protection = copy(src.protection)

    if isinstance(src.value, str) and src.value.startswith("="):

        dst.value = Translator(
            src.value,
            origin=src.coordinate
        ).translate_formula(dst.coordinate)

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
    time.perf_counter() - start_time
) * 1000


# --------------------------------------------------
# 1～12行を13～24行へコピー
# 背景色・罫線・数式を維持
# --------------------------------------------------
for r in range(1, 13):

    for c in range(1, 12):

        src = ws.cell(r, c)
        dst = ws.cell(r + 12, c)

        copy_cell(src, dst)


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
# 統計情報
# C24 = 経過時間(ms)
# --------------------------------------------------
ws["C24"] = round(elapsed_ms, 0)


# --------------------------------------------------
# 保存
# --------------------------------------------------
wb.save(OUTPUT_FILE)


print("作成完了")
print(OUTPUT_FILE)

print(
    f"elapsed_time = {elapsed_ms:.0f} ms"
)

print("----- 解答 -----")

for row in board:
    print(row)
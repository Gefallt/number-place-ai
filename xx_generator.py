from copy import copy
from openpyxl import load_workbook
from openpyxl.formula.translate import Translator

FILE_NAME = "sudoku_x_complete.xlsx"

# -----------------------------
# Workbook読込
# -----------------------------
wb = load_workbook(FILE_NAME)
ws = wb.active

# -----------------------------
# 問題読込
# B2:J10
# -----------------------------
board = []

for r in range(2, 11):

    row = []

    for c in range(2, 11):

        v = ws.cell(r, c).value

        if v is None:
            v = 0

        row.append(int(v))

    board.append(row)


# -----------------------------
# SudokuX判定
# -----------------------------
def is_valid(board, row, col, num):

    # 行
    for c in range(9):
        if board[row][c] == num:
            return False

    # 列
    for r in range(9):
        if board[r][col] == num:
            return False

    # 3x3
    br = (row // 3) * 3
    bc = (col // 3) * 3

    for r in range(br, br + 3):
        for c in range(bc, bc + 3):

            if board[r][c] == num:
                return False

    # 主対角線
    if row == col:

        for i in range(9):

            if board[i][i] == num:
                return False

    # 副対角線
    if row + col == 8:

        for i in range(9):

            if board[i][8 - i] == num:
                return False

    return True


# -----------------------------
# 空セル検索
# -----------------------------
def find_empty(board):

    for r in range(9):
        for c in range(9):

            if board[r][c] == 0:
                return r, c

    return None


# -----------------------------
# Solver
# -----------------------------
def solve(board):

    pos = find_empty(board)

    if pos is None:
        return True

    row, col = pos

    for num in range(1, 10):

        if is_valid(board, row, col, num):

            board[row][col] = num

            if solve(board):
                return True

            board[row][col] = 0

    return False


# -----------------------------
# 解答
# -----------------------------
if not solve(board):
    raise Exception("解なし")


# -----------------------------
# 上段の書式コピー
# 行1～11 → 行13～23
# -----------------------------
for r in range(1, 12):

    for c in range(1, 12):

        src = ws.cell(r, c)
        dst = ws.cell(r + 12, c)

        if src.has_style:
            dst.font = copy(src.font)
            dst.fill = copy(src.fill)
            dst.border = copy(src.border)
            dst.alignment = copy(src.alignment)
            dst.number_format = copy(src.number_format)
            dst.protection = copy(src.protection)

        # 数式もコピー
        #if isinstance(src.value, str) and src.value.startswith("="):
        #    dst.value = src.value
        #else:
        #    dst.value = src.value

        if isinstance(src.value, str) and src.value.startswith("="):

            dst.value = Translator(
                src.value,
                origin=src.coordinate
            ).translate_formula(dst.coordinate)

        else:
            dst.value = src.value

#
# from copy import copy
#from openpyxl.formula.translate import Translator
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
#
# 範囲コピー
#
for r in range(1, 12):
    for c in range(1, 12):

        copy_cell(
            ws.cell(r, c),
            ws.cell(r + 12, c)
        )
# A12～K12
for c in range(1, 12):

    copy_cell(
        ws.cell(12, c),
        ws.cell(24, c)
    )

#
# -----------------------------
# 解答出力
# B14:J22
# -----------------------------
for r in range(9):

    for c in range(9):

        ws.cell(
            row=r + 14,
            column=c + 2
        ).value = board[r][c]


# -----------------------------
# 保存
# -----------------------------
OUTPUT_FILE = "sudoku_x_completed.xlsx"

wb.save(OUTPUT_FILE)

print("作成完了")
print(OUTPUT_FILE)
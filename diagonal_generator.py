import random

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment

N = 9

board = [[0 for _ in range(N)] for _ in range(N)]

def is_valid(r, c, n):

#def is_valid(
#    r: Any,
#    c: Any,
#    n: Any
#) -> bool

    # 行
    for x in range(9):
        if board[r][x] == n:
            return False

    # 列
    for x in range(9):
        if board[x][c] == n:
            return False

    # ブロック
    br = (r // 3) * 3
    bc = (c // 3) * 3

    for rr in range(br, br + 3):
        for cc in range(bc, bc + 3):
            if board[rr][cc] == n:
                return False

    # 主対角線
    if r == c:
        for i in range(9):
            if board[i][i] == n:
                return False

    # 副対角線
    if r + c == 8:
        for i in range(9):
            if board[i][8 - i] == n:
                return False

    return True


def solve(pos=0):

    if pos == 81:
        return True

    r = pos // 9
    c = pos % 9

    nums = list(range(1, 10))
    random.shuffle(nums)

    for n in nums:

        if is_valid(r, c, n):

            board[r][c] = n

            if solve(pos + 1):
                return True

            board[r][c] = 0

    return False


solve()

for row in board:
    print(row)

print("Main Diagonal =", sum(board[i][i] for i in range(9)))
print("Sub Diagonal  =", sum(board[i][8-i] for i in range(9)))

wb = Workbook()
ws = wb.active
ws.title = "SudokuX"

# 見出し
for c in range(9):
    ws.cell(row=1, column=c + 2).value = f"R{c + 1}"

for r in range(9):
    ws.cell(row=r + 2, column=1).value = f"L{r + 1}"

yellow = PatternFill(
    fill_type="solid",
    start_color="FFFF00",
    end_color="FFFF00"
)

# 数独出力
for r in range(9):
    for c in range(9):

        cell = ws.cell(row=r + 2, column=c + 2)
        cell.value = board[r][c]
        cell.alignment = Alignment(horizontal="center")

        # 主対角線
        if r == c:
            cell.fill = yellow

        # 副対角線
        if r + c == 8:
            cell.fill = yellow

# 行合計(K列)
for r in range(9):
    ws.cell(row=r + 2, column=11).value = sum(board[r])

# 列合計(11行)
for c in range(9):
    ws.cell(row=11, column=c + 2).value = sum(
        board[r][c] for r in range(9)
    )

# K1
main_sum = sum(board[i][i] for i in range(9))
ws["K1"] = main_sum

# K11
sub_sum = sum(board[i][8-i] for i in range(9))
ws["K11"] = sub_sum

# 列幅
for col in "ABCDEFGHIJK":
    ws.column_dimensions[col].width = 8

wb.save("sudoku_x_complete.xlsx")

print("Excel出力完了")
print("sudoku_x_complete.xlsx")

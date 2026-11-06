import time
import random
import json
from copy import deepcopy


# ------------------------------------------
# 脳の重み
# ------------------------------------------
weights = {
    "candidate": 1.0,
    "row": 1.0,
    "col": 1.0,
    "box": 1.0
}


# ------------------------------------------
# 学習ファイル
# ------------------------------------------
WEIGHT_FILE = "brain_weights.json"


# ------------------------------------------
# 保存
# ------------------------------------------
def save_weights():

    with open(
        WEIGHT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(weights, f, indent=4)


# ------------------------------------------
# 読込
# ------------------------------------------
def load_weights():

    global weights

    try:

        with open(
            WEIGHT_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            weights = json.load(f)

    except:

        save_weights()


# ------------------------------------------
# 候補取得
# ------------------------------------------
def candidates(
    board,
    row,
    col
):

    result = []

    for num in range(1, 10):

        if is_valid(
            board,
            row,
            col,
            num
        ):

            result.append(num)

    return result


# ------------------------------------------
# 行既知数
# ------------------------------------------
def row_count(
    board,
    row
):

    return sum(
        1
        for v in board[row]
        if v != 0
    )


# ------------------------------------------
# 列既知数
# ------------------------------------------
def col_count(
    board,
    col
):

    count = 0

    for r in range(9):

        if board[r][col] != 0:
            count += 1

    return count


# ------------------------------------------
# ブロック既知数
# ------------------------------------------
def box_count(
    board,
    row,
    col
):

    br = (row // 3) * 3
    bc = (col // 3) * 3

    count = 0

    for r in range(br, br + 3):
        for c in range(bc, bc + 3):

            if board[r][c] != 0:
                count += 1

    return count


# ------------------------------------------
# 数独判定
# ------------------------------------------
def is_valid(
    board,
    row,
    col,
    num
):

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


# ------------------------------------------
# MRV脳
# ------------------------------------------
def select_cell(board):

    best_score = -999999
    best_pos = None
    best_candidates = None

    for r in range(9):
        for c in range(9):

            if board[r][c] != 0:
                continue

            cand = candidates(
                board,
                r,
                c
            )

            if len(cand) == 0:
                continue

            score = (

                weights["row"]
                * row_count(
                    board,
                    r
                )

                +

                weights["col"]
                * col_count(
                    board,
                    c
                )

                +

                weights["box"]
                * box_count(
                    board,
                    r,
                    c
                )

                -

                weights["candidate"]
                * len(cand)

            )

            if score > best_score:

                best_score = score
                best_pos = (
                    r,
                    c
                )

                best_candidates = cand

    return (
        best_pos,
        best_candidates
    )


# ------------------------------------------
# 解く
# ------------------------------------------
def solve(board):

    pos, cand = select_cell(board)

    if pos is None:
        return True

    row, col = pos

    for num in cand:

        board[row][col] = num

        if solve(board):
            return True

        board[row][col] = 0

    return False


# ------------------------------------------
# 学習
# ------------------------------------------
def train(
    board,
    epoch=100
):

    global weights

    load_weights()

    best_time = None
    best_weight = deepcopy(
        weights
    )

    for e in range(epoch):

        test_weight = deepcopy(
            weights
        )

        for k in test_weight:

            test_weight[k] += (
                random.random()
                - 0.5
            )

        old = deepcopy(
            weights
        )

        weights = test_weight

        work = deepcopy(
            board
        )

        start = (
            time.perf_counter()
        )

        solve(work)

        elapsed = (
            time.perf_counter()
            - start
        ) * 1000

        print(
            f"epoch={e:4d} "
            f"time={elapsed:8.3f}ms"
        )

        if (
            best_time is None
            or
            elapsed < best_time
        ):

            best_time = elapsed

            best_weight = deepcopy(
                test_weight
            )

        weights = old

    weights = best_weight

    save_weights()

    print()
    print(
        "best_time =",
        best_time
    )

    print(
        "weights =",
        weights
    )


# ------------------------------------------
# サンプル
# ------------------------------------------
board = [

    [1,0,0,0,5,0,0,0,9],
    [0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0],

    [0,3,4,0,0,7,0,0,0],
    [0,0,7,0,0,0,0,0,0],
    [0,0,0,2,0,0,0,6,0],

    [0,4,5,0,7,8,0,0,0],
    [0,7,8,0,0,0,3,0,0],
    [0,0,0,0,0,0,0,0,0]

]


train(
    board,
    epoch=100
)
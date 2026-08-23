"""ナンプレを解くCLIエントリポイント。"""

from copy import deepcopy

import board
import reporting
import solver


def main():
    # ナンプレの問題が入った81桁の文字列を入力
    input_string = input()

    reporting.reset()

    # 文字列を盤面に変換
    initial_board = deepcopy(board.parse_board(input_string))
    # 各列、各行、各エリアの候補となる数字の集合が入ったリストを作成
    column_candidates = deepcopy(board.get_column_candidates(initial_board))
    row_candidates = deepcopy(board.get_row_candidates(initial_board))
    area_candidates = deepcopy(board.get_area_candidates(initial_board))
    # ナンプレを解く
    solver.solve_number_place(
        initial_board, column_candidates, row_candidates, area_candidates
    )

    print("---result---")
    reporting.output_answer(reporting.answers[0], is_summary=True)


if __name__ == "__main__":
    main()

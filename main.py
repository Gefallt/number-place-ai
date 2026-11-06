"""ナンプレを解くCLIエントリポイント。"""

import reporting
import solver
from board import Board, parse_cells


def main():
    print("INPUT(n81)")
    # ナンプレの問題が入った81桁の文字列を入力
    input_string = input()

    reporting.reset()

    # ナンプレを解く
    board = Board(parse_cells(input_string))
    solver.solve(board)

    print("---result---")
    reporting.output_answer(reporting.answers[0], is_summary=True)


if __name__ == "__main__":
    main()

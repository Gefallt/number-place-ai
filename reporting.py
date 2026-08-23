"""解の出力と統計情報の管理。"""

import time

# 解がない盤面だったため弾いた回数
invalid_count = 0
# 見つかった解の数
answer_count = 0
# 見つかった解のリスト
answers = []
# 処理時間の計測開始時刻
start_time = 0
# solve_number_placeを呼び出した回数
solve_count = 0


def reset():
    """統計情報を初期化し、計測を開始する"""
    global invalid_count, answer_count, answers, start_time, solve_count
    invalid_count = 0
    answer_count = 0
    answers = []
    start_time = time.time()
    solve_count = 0


def output_answer(board, is_summary=False):
    """答えを出力する

    Args:
        board (numpy.ndarray): 数字のリスト
        is_summary (bool): 最終結果としての出力かどうか
    """
    global answer_count
    if not is_summary:
        answer_count += 1
    answers.append(board)
    print(board)
    print(f"time : {time.time() - start_time:.3f}s")
    print(f"count:{solve_count}")
    print(f"no_cnt: {invalid_count}")
    print(f"ans_cnt: {answer_count}")

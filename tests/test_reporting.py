import numpy as np

import reporting


def test_reset_initializes_state():
    reporting.invalid_count = 5
    reporting.answer_count = 3
    reporting.answers = [1, 2, 3]
    reporting.solve_count = 10

    reporting.reset()

    assert reporting.invalid_count == 0
    assert reporting.answer_count == 0
    assert reporting.answers == []
    assert reporting.solve_count == 0
    assert reporting.start_time > 0


def test_output_answer_increments_count_by_default(capsys):
    reporting.reset()
    board = np.zeros((9, 9), dtype=int)

    reporting.output_answer(board)

    assert reporting.answer_count == 1
    assert reporting.answers == [board]
    captured = capsys.readouterr()
    assert "count:" in captured.out
    assert "no_cnt:" in captured.out
    assert "ans_cnt: 1" in captured.out


def test_output_answer_summary_does_not_increment_count(capsys):
    reporting.reset()
    board = np.zeros((9, 9), dtype=int)
    reporting.output_answer(board)

    reporting.output_answer(board, is_summary=True)

    assert reporting.answer_count == 1  # 2回目はカウントされない
    assert reporting.answers == [board, board]
    captured = capsys.readouterr()
    assert "ans_cnt: 1" in captured.out

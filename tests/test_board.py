import numpy as np
import pytest

from board import BOARD_SIZE, FULL_MASK, Board, box_index, iter_values, parse_cells

EMPTY_CELLS = [0] * (BOARD_SIZE * BOARD_SIZE)


@pytest.mark.parametrize(
    "row, col, expected",
    [
        (0, 0, 0),
        (0, 8, 2),
        (3, 6, 5),
        (8, 8, 8),
        (4, 4, 4),
    ],
)
def test_box_index(row, col, expected):
    assert box_index(row, col) == expected


def test_iter_values_empty_mask_yields_nothing():
    assert list(iter_values(0)) == []


def test_iter_values_yields_ascending_values():
    mask = (1 << 0) | (1 << 2) | (1 << 8)  # 数字1, 3, 9
    assert list(iter_values(mask)) == [1, 3, 9]


def test_iter_values_single_bit():
    assert list(iter_values(1 << 4)) == [5]


def test_parse_cells():
    input_string = "5" + "0" * 79 + "9"
    cells = parse_cells(input_string)
    assert cells[0] == 5
    assert cells[-1] == 9
    assert cells[1:-1] == [0] * 79
    assert len(cells) == 81


def test_board_init_all_empty_has_full_candidates():
    board = Board(list(EMPTY_CELLS))
    for row in range(BOARD_SIZE):
        assert board.row_masks[row] == FULL_MASK
        assert board.col_masks[row] == FULL_MASK
        assert board.box_masks[row] == FULL_MASK
    assert board.candidate_mask(0, 0) == FULL_MASK


def test_board_init_clears_candidates_for_given_values():
    cells = list(EMPTY_CELLS)
    cells[0] = 5  # (row=0, col=0)
    board = Board(cells)
    bit5 = 1 << 4
    assert board.row_masks[0] & bit5 == 0
    assert board.col_masks[0] & bit5 == 0
    assert board.box_masks[0] & bit5 == 0
    # 他の行・列・エリアには影響しない
    assert board.row_masks[1] == FULL_MASK
    assert board.col_masks[1] == FULL_MASK


def test_assign_then_unassign_round_trip():
    board = Board(list(EMPTY_CELLS))
    before = (
        list(board.row_masks),
        list(board.col_masks),
        list(board.box_masks),
    )
    board.assign(2, 3, 7)
    assert board.cells[2 * BOARD_SIZE + 3] == 7
    bit7 = 1 << 6
    assert board.candidate_mask(2, 3) & bit7 == 0

    board.unassign(2, 3, 7)
    assert board.cells[2 * BOARD_SIZE + 3] == 0
    after = (list(board.row_masks), list(board.col_masks), list(board.box_masks))
    assert before == after


def test_candidate_mask_reflects_row_col_box_intersection():
    cells = list(EMPTY_CELLS)
    cells[0] = 1  # row0, col0
    cells[1] = 2  # row0, col1
    cells[9] = 3  # row1, col0
    board = Board(cells)
    # row2, col2は同じエリア(box0)なので1,2,3は候補から外れる
    mask = board.candidate_mask(2, 2)
    for value in (1, 2, 3):
        assert mask & (1 << (value - 1)) == 0
    assert mask & (1 << (4 - 1)) != 0


def test_eliminate_removes_new_bits_and_logs_change():
    board = Board(list(EMPTY_CELLS))
    changes = []
    bits = (1 << 0) | (1 << 1)  # 候補1, 2

    result = board.eliminate(0, 0, bits, changes)

    assert result is True
    assert board.eliminated[0] == bits
    assert changes == [("eliminate", 0, 0, bits)]


def test_eliminate_returns_false_when_nothing_new():
    board = Board(list(EMPTY_CELLS))
    changes = []
    bits = 1 << 0
    board.eliminate(0, 0, bits, changes)

    result = board.eliminate(0, 0, bits, changes)

    assert result is False
    assert changes == [("eliminate", 0, 0, bits)]  # 2回目は追加されない


def test_eliminate_partial_overlap_only_logs_new_bits():
    board = Board(list(EMPTY_CELLS))
    changes = []
    board.eliminate(0, 0, 1 << 0, changes)

    result = board.eliminate(0, 0, (1 << 0) | (1 << 1), changes)

    assert result is True
    assert board.eliminated[0] == (1 << 0) | (1 << 1)
    assert changes[-1] == ("eliminate", 0, 0, 1 << 1)


def test_restore_undoes_eliminate():
    board = Board(list(EMPTY_CELLS))
    changes = []
    bits = (1 << 0) | (1 << 1)
    board.eliminate(0, 0, bits, changes)

    board.restore(0, 0, bits)

    assert board.eliminated[0] == 0
    assert board.candidate_mask(0, 0) == FULL_MASK


def test_restore_only_clears_given_bits():
    board = Board(list(EMPTY_CELLS))
    changes = []
    board.eliminate(0, 0, (1 << 0) | (1 << 1), changes)

    board.restore(0, 0, 1 << 0)

    assert board.eliminated[0] == 1 << 1


def test_to_numpy_matches_cells():
    cells = list(range(81))
    board = Board(cells)
    array = board.to_numpy()
    assert isinstance(array, np.ndarray)
    assert array.shape == (9, 9)
    assert array[0][0] == 0
    assert array[8][8] == 80

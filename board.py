"""ナンプレの盤面表現(ビットマスクで候補を管理する)。"""

import numpy as np

BOARD_SIZE = 9
BLOCK_SIZE = 3
# 1〜9すべてが候補であることを表すビットマスク(0b111111111)
FULL_MASK = (1 << BOARD_SIZE) - 1

# 0〜FULL_MASKの各値について、立っているビット数(候補の数)を引けるようにした表
POPCOUNT = [bin(mask).count("1") for mask in range(1 << BOARD_SIZE)]


def box_index(row, col):
    """(row, col) が属するエリア(3x3ブロック)の番号を返す"""
    return (row // BLOCK_SIZE) * BLOCK_SIZE + col // BLOCK_SIZE


def iter_values(mask):
    """ビットマスクに立っている候補を数字(1〜9)として1つずつ返す"""
    while mask:
        low_bit = mask & -mask
        yield low_bit.bit_length()
        mask ^= low_bit


def parse_cells(input_string):
    """81桁の数字文字列を、マスごとの数字が入ったフラットなリストに変換する

    Args:
        input_string (str): 81桁の数字文字列(0は空マス)

    Returns:
        list: 81個の数字が入ったリスト(行優先)
    """
    return [int(char) for char in input_string]


class Board:
    """ビットマスクで候補を管理する9x9ナンプレの盤面

    row_masks[row] のbit (v-1) が立っていれば、数字 v がまだその行に
    置かれていないことを表す。col_masks・box_masksも同様。

    eliminated[idx] は、行・列・エリアの制約(row_masks等)だけからは
    導けない追加の候補除外(naked pair・pointing pairなど)を表す。
    """

    def __init__(self, cells):
        self.cells = cells
        self.row_masks = [FULL_MASK] * BOARD_SIZE
        self.col_masks = [FULL_MASK] * BOARD_SIZE
        self.box_masks = [FULL_MASK] * BOARD_SIZE
        self.eliminated = [0] * (BOARD_SIZE * BOARD_SIZE)
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                value = cells[row * BOARD_SIZE + col]
                if value != 0:
                    self._clear_candidate(row, col, value)

    def _clear_candidate(self, row, col, value):
        bit = 1 << (value - 1)
        self.row_masks[row] &= ~bit
        self.col_masks[col] &= ~bit
        self.box_masks[box_index(row, col)] &= ~bit

    def _restore_candidate(self, row, col, value):
        bit = 1 << (value - 1)
        self.row_masks[row] |= bit
        self.col_masks[col] |= bit
        self.box_masks[box_index(row, col)] |= bit

    def candidate_mask(self, row, col):
        """(row, col) に置ける数字のビットマスクを返す"""
        idx = row * BOARD_SIZE + col
        return (
            self.row_masks[row]
            & self.col_masks[col]
            & self.box_masks[box_index(row, col)]
            & ~self.eliminated[idx]
        )

    def assign(self, row, col, value):
        """(row, col) に value を置く"""
        self.cells[row * BOARD_SIZE + col] = value
        self._clear_candidate(row, col, value)

    def unassign(self, row, col, value):
        """assign(row, col, value) を取り消す"""
        self.cells[row * BOARD_SIZE + col] = 0
        self._restore_candidate(row, col, value)

    def eliminate(self, row, col, bits, changes):
        """(row, col) の候補から bits を追加で取り除く

        行・列・エリアの制約(row_masks等)だけでは導けない除外を記録する。
        実際に新しく取り除けたビットがあった場合はTrueを返し、
        undo用にchangesへ記録する。

        Args:
            row (int): 行番号
            col (int): 列番号
            bits (int): 取り除く候補のビットマスク
            changes (list): このsolve呼び出し内での変更を記録するログ

        Returns:
            bool: 何か新しく取り除けたらTrue
        """
        idx = row * BOARD_SIZE + col
        new_bits = bits & ~self.eliminated[idx]
        if new_bits == 0:
            return False
        self.eliminated[idx] |= new_bits
        changes.append(("eliminate", row, col, new_bits))
        return True

    def restore(self, row, col, bits):
        """eliminate(row, col, bits, ...) を取り消す"""
        idx = row * BOARD_SIZE + col
        self.eliminated[idx] &= ~bits

    def to_numpy(self):
        """出力表示用に9x9のnumpy配列へ変換する"""
        return np.array(
            [
                self.cells[row * BOARD_SIZE : (row + 1) * BOARD_SIZE]
                for row in range(BOARD_SIZE)
            ]
        )

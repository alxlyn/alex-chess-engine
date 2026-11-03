import chess
import pytest

from engine.search import choose_move

MATE_IN_ONE = [
    "8/k7/8/8/8/8/8/1RQK4 w - - 0 1",
    "4K3/8/8/7k/8/8/6Q1/3R4 w - - 0 1",
    "8/2K3R1/1Q6/8/8/8/8/7k w - - 0 1",
]


@pytest.mark.parametrize("fen", MATE_IN_ONE)
def test_plays_mate_in_one(fen):
    board = chess.Board(fen)
    board.push(choose_move(board, depth=3))
    assert board.is_checkmate()
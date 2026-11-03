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


def test_a_repeated_position_is_a_draw_in_search():
    from engine.search import INF, negamax

    board = chess.Board("4k3/8/8/8/8/8/3Q4/4K3 w - - 0 1")
    for move in ["d2c2", "e8f8", "c2d2", "f8e8"]:
        board.push_uci(move)
    assert negamax(board, 2, -INF, INF) == 0

# Best moves at depth 3, recorded before the draw checks were made cheaper.
# A speed change must not change what the engine plays.
REFERENCE = [
    (chess.STARTING_FEN, "g1f3"),
    ("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3", "b1c3"),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", "e2a6"),
    ("r2q1rk1/pp2bppp/2n1bn2/2pp4/3P4/2PBPN2/PP1N1PPP/R2QK2R w KQ - 0 10", "d1b3"),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", "b4f4"),
]


@pytest.mark.parametrize("fen,expected", REFERENCE)
def test_same_best_move_as_before(fen, expected):
    assert choose_move(chess.Board(fen), depth=3).uci() == expected
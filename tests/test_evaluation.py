import chess

from engine.evaluation import evaluate_white


def score(fen: str) -> int:
    return evaluate_white(chess.Board(fen))


def test_start_position_is_equal():
    assert score(chess.STARTING_FEN) == 0


def test_white_pawn_is_worth_more_further_up_the_board():
    on_e2 = score("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
    on_e7 = score("4k3/4P3/8/8/8/8/8/4K3 w - - 0 1")
    assert on_e7 > on_e2


def test_white_king_prefers_its_own_back_rank():
    # A rook each, so the position isn't a dead draw (which scores 0).
    on_g1 = score("r3k3/8/8/8/8/8/8/R5K1 w - - 0 1")
    on_g8 = score("r3k1K1/8/8/8/8/8/8/R7 w - - 0 1")
    assert on_g1 > on_g8


def test_black_mirrors_white():
    white_pawn_e2 = score("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
    black_pawn_e7 = score("4k3/4p3/8/8/8/8/8/4K3 w - - 0 1")
    assert white_pawn_e2 == -black_pawn_e7

def test_repetition_does_not_wipe_out_material():
    board = chess.Board("4k3/8/8/8/8/8/3Q4/4K3 w - - 0 1")
    for move in ["d2c2", "e8f8", "c2d2", "f8e8"]:
        board.push_uci(move)
    assert evaluate_white(board) > 800
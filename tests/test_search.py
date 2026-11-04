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


def test_captures_come_first_without_a_table_move():
    from engine.search import ordered_moves

    board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3")
    assert board.is_capture(ordered_moves(board)[0])


def test_root_best_move_is_kept_for_the_next_depth():
    from engine.search import TT, tt_key

    board = chess.Board(chess.STARTING_FEN)
    move = choose_move(board, depth=2)
    assert TT[tt_key(board)][3] == move.uci()


def test_mate_scores_are_stored_from_the_node_and_read_back_at_any_ply():
    from engine.search import INF, MATE, TT, negamax, tt_key

    board = chess.Board(MATE_IN_ONE[0])  # White mates in one
    assert negamax(board, 2, -INF, INF, ply=3) == MATE - 4  # the mate lands on ply 4
    assert TT[tt_key(board)][2] == MATE - 1  # stored as "mate in one from here"
    assert negamax(board, 2, -INF, INF, ply=5) == MATE - 6  # read from the table at ply 5


def test_the_table_move_is_tried_first():
    from engine.search import TT, ordered_moves, tt_key

    board = chess.Board()
    TT[tt_key(board)] = (1, "EXACT", 0, "a2a3")
    assert ordered_moves(board)[0] == chess.Move.from_uci("a2a3")


def test_fifty_moves_without_a_capture_is_a_draw():
    from engine.search import INF, negamax

    board = chess.Board("4k3/8/8/8/8/8/3Q4/4K3 w - - 100 80")
    assert negamax(board, 2, -INF, INF) == 0


def test_a_mate_found_in_quiescence_is_scored_by_distance():
    from engine.search import INF, MATE, quiescence

    board = chess.Board("4r2k/6pp/8/8/8/8/6PP/4R1K1 w - - 0 1")  # Rxe8 is mate
    assert quiescence(board, -INF, INF, ply=3) == MATE - 4


def test_a_stored_lower_bound_at_or_above_beta_cuts_off():
    from engine.search import INF, TT, negamax, tt_key

    board = chess.Board()
    TT[tt_key(board)] = (5, "LOWER", 500, None)  # searched deeper before: worth at least 500
    assert negamax(board, 2, -INF, 400) >= 400


def test_a_stored_upper_bound_at_or_below_alpha_cuts_off():
    from engine.search import INF, TT, negamax, tt_key

    board = chess.Board()
    TT[tt_key(board)] = (5, "UPPER", -500, None)  # worth at most -500
    assert negamax(board, 2, -400, INF) <= -400


def test_a_shallower_entry_is_not_trusted():
    from engine.search import INF, TT, negamax, tt_key

    board = chess.Board()
    TT[tt_key(board)] = (1, "EXACT", 12345, None)
    assert negamax(board, 2, -INF, INF) != 12345


def test_losing_mate_scores_convert_both_ways():
    from engine.search import MATE, from_tt, to_tt

    assert to_tt(-(MATE - 5), 3) == -(MATE - 2)
    assert from_tt(to_tt(-(MATE - 5), 3), 3) == -(MATE - 5)


def test_quiescence_tries_pawn_takes_queen_before_queen_takes_pawn():
    from engine.search import _capture_moves

    board = chess.Board("k7/8/8/3q3p/2P5/8/8/K6Q w - - 0 1")
    assert _capture_moves(board)[0] == chess.Move.from_uci("c4d5")


def test_a_bound_from_the_table_doesnt_become_the_score():
    from engine.search import INF, TT, negamax, tt_key

    board = chess.Board()
    true_score = negamax(board, 2, -INF, INF)
    TT.clear()
    TT[tt_key(board)] = (5, "UPPER", -50, None)  # only says "at most -50"
    assert negamax(board, 2, -INF, INF) == true_score


def test_a_fail_low_is_stored_as_an_upper_bound():
    from engine.search import TT, negamax, tt_key

    board = chess.Board()
    negamax(board, 2, 1000, 1001)  # nothing reaches +1000
    _, flag, value, _ = TT[tt_key(board)]
    assert flag == "UPPER" and value <= 1000


def test_a_fail_high_is_stored_as_a_lower_bound():
    from engine.search import TT, negamax, tt_key

    board = chess.Board()
    negamax(board, 2, -1001, -1000)  # everything beats -1000
    _, flag, value, _ = TT[tt_key(board)]
    assert flag == "LOWER" and value >= -1000


def test_stalemate_scores_zero():
    from engine.search import INF, negamax

    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")  # Black has no moves and isn't in check
    assert negamax(board, 1, -INF, INF) == 0


def test_castling_rights_are_part_of_the_table_key():
    from engine.search import tt_key

    with_rights = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    without = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1")
    assert tt_key(with_rights) != tt_key(without)
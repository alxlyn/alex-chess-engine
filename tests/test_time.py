import chess
import pytest

from engine import search

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def fake_clock(expire_after_calls: int):
    """A clock that reads 0 for the first N calls, then jumps far past any deadline."""
    calls = {"n": 0}

    def clock():
        calls["n"] += 1
        return 0.0 if calls["n"] <= expire_after_calls else 1e9

    return clock


@pytest.mark.parametrize("expire_after", [2, 5, 50, 500])
def test_timeout_still_returns_a_legal_move(monkeypatch, expire_after):
    monkeypatch.setattr(search, "clock", fake_clock(expire_after))
    board = chess.Board(KIWIPETE)
    move = search.choose_move_timed(board, time_limit_s=1.0)
    assert move in board.legal_moves


def test_timeout_leaves_the_board_unchanged(monkeypatch):
    monkeypatch.setattr(search, "clock", fake_clock(50))
    board = chess.Board(KIWIPETE)
    search.choose_move_timed(board, time_limit_s=1.0)
    assert board.fen() == KIWIPETE
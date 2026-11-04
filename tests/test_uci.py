import subprocess
import sys
from pathlib import Path

import chess
import pytest

from engine import search
from uci import handle, pick_time_limit

UCI_PY = Path(__file__).resolve().parent.parent / "uci.py"


def run_uci(*commands: str) -> list[str]:
    """Start uci.py, send the commands, return its output lines. Fails instead of hanging."""
    result = subprocess.run(
        [sys.executable, str(UCI_PY)],
        input="\n".join([*commands, "quit"]) + "\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.splitlines()


def test_depth_zero_still_answers():
    assert any(line.startswith("bestmove") for line in run_uci("position startpos", "go depth 0"))


def test_no_legal_moves_gives_null_move():
    out = run_uci("position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1", "go depth 2")
    assert "bestmove 0000" in out


def test_bad_input_does_not_kill_the_engine():
    out = run_uci("position fen not a fen", "position startpos moves e2e5", "go movetime", "isready")
    assert "readyok" in out


def test_go_without_a_number_still_answers():
    out = run_uci("position startpos", "go movetime")
    assert any(line.startswith("bestmove") for line in out)


def test_a_bad_position_is_not_answered_with_the_old_board():
    out = run_uci("position startpos", "position startpos moves e2e4 zz", "go depth 1")
    assert "bestmove 0000" in out


def test_a_tiny_clock_is_never_overspent():
    limit = pick_time_limit(chess.Board(), "go wtime 10 btime 10".split())
    assert limit <= 0.0025


BLACK_TO_MOVE = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


@pytest.mark.parametrize("fen,command,seconds", [
    (chess.STARTING_FEN, "go movetime 200", 0.2),
    (chess.STARTING_FEN, "go wtime 60050 btime 1050", 2.0),                 # (60050 - 50) / 30 ms
    (BLACK_TO_MOVE, "go wtime 60050 btime 3050", 0.1),                      # Black uses its own clock
    (chess.STARTING_FEN, "go wtime 60050 btime 60050 winc 1000 binc 0", 2.5),  # plus half the increment
    (chess.STARTING_FEN, "go wtime 40 btime 40", 0.0),                      # all of it is reserve
])
def test_time_limits(fen, command, seconds):
    assert pick_time_limit(chess.Board(fen), command.split()) == pytest.approx(seconds)


def test_ucinewgame_clears_the_table():
    search.choose_move(chess.Board(), depth=2)
    assert search.TT
    handle("ucinewgame", chess.Board())
    assert not search.TT


def test_the_cap_holds_when_the_increment_is_bigger_than_the_clock():
    limit = pick_time_limit(chess.Board(), "go wtime 1050 btime 1050 winc 2000 binc 2000".split())
    assert limit == pytest.approx(0.25)  # a quarter of the 1000 ms left, not 1033 ms


def test_go_still_answers_when_the_search_crashes(monkeypatch, capsys):
    import io

    import uci

    def broken_search(*args, **kwargs):
        raise RuntimeError("search bug")

    monkeypatch.setattr(uci, "choose_move", broken_search)
    monkeypatch.setattr("sys.stdin", io.StringIO("position startpos\ngo depth 2\nquit\n"))
    uci.uci_loop()
    out = capsys.readouterr().out.splitlines()
    assert any(line.startswith("bestmove ") and line != "bestmove 0000" for line in out)
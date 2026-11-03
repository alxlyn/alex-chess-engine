#!/usr/bin/env python3

import sys
import chess

from engine.search import TT, choose_move, choose_move_timed

ENGINE_NAME = "alex-chess-engine"
AUTHOR = "Alex"

# UCI front end: reads commands from a chess GUI on stdin and answers on stdout.
def parse_position(cmd: str) -> chess.Board:
    parts = cmd.split()
    board = chess.Board()

    if "startpos" in parts:
        board = chess.Board()
        moves_index = parts.index("startpos") + 1

    elif "fen" in parts:
        fen_index = parts.index("fen") + 1
        fen = " ".join(parts[fen_index:fen_index + 6])
        board = chess.Board(fen)
        moves_index = fen_index + 6

    else:
        return board
    if moves_index < len(parts) and parts[moves_index] == "moves":
        for mv in parts[moves_index + 1:]:
            board.push_uci(mv)

    return board

def int_after(parts: list[str], key: str, default: int | None = None) -> int | None:
    """The number after `key` in a command, or `default` if it's missing or not a number."""
    try:
        return int(parts[parts.index(key) + 1])
    except (ValueError, IndexError):
        return default

# Basic time management:
def pick_time_limit(board: chess.Board, parts: list[str]) -> float | None:
    movetime = int_after(parts, "movetime")
    if movetime is not None:
        return max(0.01, movetime / 1000.0)

    # Use remaining time if provided
    wtime = int_after(parts, "wtime")
    btime = int_after(parts, "btime")
    winc = int_after(parts, "winc", 0)
    binc = int_after(parts, "binc", 0)

    if wtime is None or btime is None:
        return None

    # Pick a time limit based on remaining time and increment. 
    time_ms = wtime if board.turn == chess.WHITE else btime
    inc_ms = winc if board.turn == chess.WHITE else binc

    # time buget: 1/30 of remaining time + 50% of increment
    think_ms = (time_ms / 30.0) + (0.5 * inc_ms)
    think_ms = max(think_ms, 20)
    # The cap comes last, so even a clock under 80 ms is never overspent.
    think_ms = min(think_ms, time_ms * 0.25)

    return think_ms / 1000.0

def handle(line: str, board: chess.Board | None, default_depth: int = 3) -> chess.Board | None:
    """Run one UCI command and return the (possibly new) board.

    The board is None after a position command that failed, so the engine
    doesn't answer for a position the GUI never sent.
    """
    if line == "uci":
        print(f"id name {ENGINE_NAME}")
        print(f"id author {AUTHOR}")
        print("uciok", flush=True)

    elif line == "isready":
        print("readyok", flush=True)

    elif line == "ucinewgame":
        TT.clear()
        return chess.Board()

    elif line.startswith("position"):
        return parse_position(line)

    elif line.startswith("go"):
        if board is None or not any(board.legal_moves):
            print("bestmove 0000", flush=True)
            return board

        parts = line.split()
        depth = int_after(parts, "depth", default_depth)

        # Time mode takes precedence over depth mode.
        time_limit = pick_time_limit(board, parts)
        if time_limit is not None:
            move = choose_move_timed(board, time_limit)
        else:
            move = choose_move(board, depth=depth)
        print(f"bestmove {move.uci()}", flush=True)

    return board


# The main UCI loop: read a command, run it, repeat. A bad command prints an error
# instead of killing the engine, because a crash loses the game.
def uci_loop():
    board = chess.Board()
    for raw in sys.stdin:
        line = raw.strip()
        if line == "quit":
            break
        try:
            board = handle(line, board)
        except Exception as exc:  # report and keep going
            print(f"info string error: {exc!r}", flush=True)
            if line.startswith("position"):
                board = None
            elif line.startswith("go"):
                # The GUI waits for a bestmove, so always send one.
                move = next(iter(board.legal_moves), None) if board else None
                print(f"bestmove {move.uci() if move else '0000'}", flush=True)


if __name__ == "__main__":
    uci_loop()

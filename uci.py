#!/Users/alxlyan/Desktop/alex-chess-engine/.venv/bin/python

import sys
import chess

from engine.search import choose_move, choose_move_timed

ENGINE_NAME = "alex-chess-engine"
AUTHOR = "Alex"


def parse_position(cmd: str) -> chess.Board:
    parts = cmd.split()
    board = chess.Board()

    # position startpos moves ...
    if "startpos" in parts:
        board = chess.Board()
        moves_index = parts.index("startpos") + 1

    # position fen <fen> moves ...
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


def pick_time_limit(board: chess.Board, parts: list[str]) -> float | None:
    """
    Basic time management:
    - If movetime is provided, use it.
    - Else if wtime/btime provided, use a small fraction of remaining time.
    Returns seconds or None.
    """
    if "movetime" in parts:
        ms = int(parts[parts.index("movetime") + 1])
        return max(0.01, ms / 1000.0)

    # Use remaining time if provided
    wtime = btime = None
    winc = binc = 0

    if "wtime" in parts:
        wtime = int(parts[parts.index("wtime") + 1])
    if "btime" in parts:
        btime = int(parts[parts.index("btime") + 1])
    if "winc" in parts:
        winc = int(parts[parts.index("winc") + 1])
    if "binc" in parts:
        binc = int(parts[parts.index("binc") + 1])

    if wtime is None or btime is None:
        return None

    # pick side-to-move time
    time_ms = wtime if board.turn == chess.WHITE else btime
    inc_ms = winc if board.turn == chess.WHITE else binc

    # very simple budgeting: 1/30 of remaining time + 50% of increment
    think_ms = (time_ms / 30.0) + (0.5 * inc_ms)
    think_ms = min(think_ms, time_ms * 0.25)  # never spend >25% of remaining
    think_ms = max(think_ms, 20)              # at least 20ms

    return think_ms / 1000.0


def uci_loop():
    board = chess.Board()
    default_depth = 3

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()

        if line == "uci":
            print(f"id name {ENGINE_NAME}")
            print(f"id author {AUTHOR}")
            print("uciok", flush=True)

        elif line == "isready":
            print("readyok", flush=True)

        elif line == "ucinewgame":
            board.reset()

        elif line.startswith("position"):
            board = parse_position(line)

        elif line.startswith("go"):
            parts = line.split()

            # Depth mode
            depth = default_depth
            if "depth" in parts:
                depth = int(parts[parts.index("depth") + 1])

            # Time mode (movetime or clocks)
            time_limit = pick_time_limit(board, parts)

            if time_limit is not None:
                move = choose_move_timed(board, time_limit)
            else:
                move = choose_move(board, depth=depth)

            print(f"bestmove {move.uci()}", flush=True)

        elif line == "quit":
            break

        sys.stdout.flush()


if __name__ == "__main__":
    uci_loop()

import sys
import chess
import time
from engine.search import choose_move
from engine.search import choose_move_timed

ENGINE_NAME = "AlexChessEngine"
AUTHOR = "Alex"

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
            parts = line.split()
            idx = 1

            if parts[idx] == "startpos":
                board = chess.Board()
                idx += 1
            elif parts[idx] == "fen":
                fen = " ".join(parts[idx + 1: idx + 7])
                board = chess.Board(fen)
                idx += 7

            if idx < len(parts) and parts[idx] == "moves":
                for mv in parts[idx + 1:]:
                    board.push_uci(mv)

        elif line.startswith("go"):
            parts = line.split()

            # Defaults
            depth = None
            movetime_ms = None

            if "depth" in parts:
                depth = int(parts[parts.index("depth") + 1])
            if "movetime" in parts:
                movetime_ms = int(parts[parts.index("movetime") + 1])

            if movetime_ms is not None:
                move = choose_move_timed(board, movetime_ms / 1000.0)
            else:
                move = choose_move(board, depth=depth or default_depth)

            print(f"bestmove {move.uci()}", flush=True)

        elif line == "quit":
            break

        sys.stdout.flush()

if __name__ == "__main__":
    uci_loop()

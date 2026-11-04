"""Times the search on five middlegame positions. The README's numbers come from this."""
import time

import chess

from engine import search

POSITIONS = [
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",  # Kiwipete
    "r2q1rk1/pp2bppp/2n1bn2/2pp4/3P4/2PBPN2/PP1N1PPP/R2QK2R w KQ - 0 10",
    "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8",
    "2rq1rk1/pp1bppbp/2np1np1/8/3NP3/1BN1BP2/PPPQ2PP/2KR3R b - - 0 11",
    "r1b2rk1/2q1bppp/p2p1n2/np2p3/3PP3/5N1P/PPBN1PP1/R1BQR1K1 w - - 0 12",
]


def main():
    for depth in (3, 4):
        times = []
        for fen in POSITIONS:
            search.TT.clear()
            start = time.perf_counter()
            search.choose_move(chess.Board(fen), depth=depth)
            times.append(time.perf_counter() - start)
        print(f"depth {depth}: " + ", ".join(f"{t:.2f}s" for t in times))

    for budget in (0.5, 1.5):
        reached = []
        for fen in POSITIONS:
            search.TT.clear()
            board = chess.Board(fen)
            deadline = search.clock() + budget * 0.97
            done = 0
            for depth in range(1, 7):
                try:
                    search.choose_move(board, depth=depth, deadline=deadline)
                except search.SearchTimeout:
                    break
                done = depth
                if search.clock() >= deadline:
                    break
            reached.append(done)
        print(f"{budget}s per move reaches depth: {reached}")


if __name__ == "__main__":
    main()

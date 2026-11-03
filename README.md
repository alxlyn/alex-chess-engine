# alex-chess-engine

A UCI chess engine in Python that I wrote to learn how engines search. It uses negamax with alpha-beta pruning, iterative deepening under a clock, quiescence search and a transposition table. The engine itself is about 490 lines.

![Engine demo](assets/ENGINE_DEMO.gif)

## How the search works

The engine searches to depth 1, then 2, then 3, and keeps the best move from the last depth it finished. On a clock you don't know how long the next depth will take, so this way there is always a complete answer when time runs out. Under UCI time controls a move gets `remaining/30 + increment/2`, capped at a quarter of the remaining time. A deadline check inside the search raises `TimeoutError` at 97% of that budget, and the unfinished depth is thrown away. If even depth 1 runs out of time, it plays the best move it had searched so far. The search works on a copy of the board, so a timeout never leaves half a line pushed on the real one.

Negamax scores every position from the side to move and negates the child's score, so min and max share one function. Alpha-beta cuts branches that can't change the result, which is what makes depth 3 or 4 possible in Python at all.

Pruning works better when good moves come first. Every node tries the transposition table's stored move first, then captures, then checks, then quiet moves. After each depth the root saves its best move in the table, so the next depth starts with it. Quiescence orders captures by MVV-LVA, so taking a queen with a pawn is looked at before taking a pawn with a queen.

At depth 0 the engine keeps searching captures, up to 8 more plies, until the position is quiet. Without that it would stop in the middle of an exchange and evaluate a position where a queen is about to be lost.

The transposition table is a dict keyed on the first four FEN fields (pieces, side to move, castling rights and en passant square). Each entry stores the depth, score, a bound flag (`EXACT`, `LOWER` or `UPPER`) and the best move. FEN keys are slower than Zobrist hashing, but they were easier to get right and to debug. A mate is scored by how many plies away it is, so the engine goes for the fastest one. The table stores mate scores relative to the position, so they stay right when the same position comes up at a different ply.

Evaluation is material plus the piece-square tables from Tomasz Michniewski's Simplified Evaluation Function (Chess Programming Wiki). Checkmate, stalemate, repetition, the 50-move rule and insufficient material are handled in the search, before the table is read. The evaluation is deliberately simple because the search was the part I wanted to learn.

## Measured behavior

- Iterative deepening stops at depth 6, which it doesn't reach in practice. Fixed-depth mode defaults to depth 3.
- On an M2, five middlegame positions take 0.4 to 1.4 seconds at depth 3 and 3 to 7 seconds at depth 4, starting from an empty transposition table. With 1.5 seconds per move the timed search finishes depth 3 on all five. With 0.5 seconds it reaches depth 1 to 3, and Kiwipete is the slowest.
- The old version called `can_claim_draw()` at every node, which tries every legal move to look for a repetition. Replacing it with cheaper draw checks and fixing the move ordering made depth 3 between 3 and 19 times faster on those five positions. Kiwipete went from 27 seconds to 1.4.
- The demo above is the engine playing Stockfish 15.1 in Banksia on a 1-minute clock. It has no opening book or endgame tables and it won't beat Stockfish. I haven't measured its Elo.

## Known issues

- The transposition table key doesn't include move history. Repeated positions are scored before the table is read, but a stored score can still come from a line that had a repetition in it.
- Quiescence only follows captures, so it can miss checks and promotions at the horizon.
- The UCI loop doesn't print `info` lines or support `stop` and `go infinite` yet.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

There are 32 tests, and GitHub Actions runs them on every push. Most of them come from bugs a code review found in November: on a short clock the engine could answer with a move for the wrong side, at depth 3 it missed some mates in one, and White read the piece-square tables upside down. They check piece-square values, mate in one, mate scores in the transposition table, a fake clock that runs out mid-search, repetition and the 50-move rule, move ordering, and the UCI loop (depth 0, no legal moves, bad input, a tiny clock).

## Running it

```bash
git clone https://github.com/alxlyn/alex-chess-engine.git
cd alex-chess-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

In Banksia or any other UCI GUI, add a new engine with the venv's Python as the command and `uci.py` as the argument:

```
Command:   /path/to/alex-chess-engine/.venv/bin/python
Argument:  /path/to/alex-chess-engine/uci.py
```

The engine supports `uci`, `isready`, `ucinewgame`, `position startpos|fen ... moves ...`, `go depth N`, `go movetime <ms>` and clock mode with `go wtime/btime [winc/binc]`. When a clock is given it takes precedence over depth. A command it can't parse gets an `info string` error, and `go` always answers with a `bestmove`.

From the terminal:

```bash
python uci.py     # UCI loop on stdin/stdout, type the commands yourself
python main.py    # the engine plays itself and prints each move
```

## Project layout

```
engine/
  search.py      # negamax, alpha-beta, quiescence, move ordering, TT, iterative deepening
  evaluation.py  # material + piece-square tables
uci.py           # UCI protocol loop and time-control parsing
main.py          # self-play
tests/           # pytest suite
```

## Requirements

Python 3.10 or newer and [python-chess](https://python-chess.readthedocs.io/), which handles the board, legal move generation and FEN. Search, evaluation, move ordering and the UCI layer live in this repo.

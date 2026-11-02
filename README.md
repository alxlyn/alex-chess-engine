# alex-chess-engine

A UCI chess engine in Python that I wrote to learn how engines search. It uses negamax with alpha-beta pruning, iterative deepening under a clock, quiescence search and a transposition table. The whole thing is about 450 lines.

![Engine demo](assets/ENGINE_DEMO.gif)

## How the search works

The engine searches to depth 1, then 2, then 3, and keeps the best move from the last depth it finished. On a clock you don't know how long the next depth will take, so this way there is always a complete answer when time runs out. Under UCI time controls a move gets `remaining/30 + increment/2`, capped at a quarter of the remaining time. A deadline check inside the search raises `TimeoutError` at 97% of that budget, and the unfinished depth is thrown away.

Negamax scores every position from the side to move and negates the child's score, so min and max share one function. Alpha-beta cuts branches that can't change the result, which is what makes depth 3 or 4 possible in Python at all.

Pruning works better when good moves come first. The main search tries the transposition table's stored move first, then captures and checks, then quiet moves. Quiescence orders captures by MVV-LVA, so taking a queen with a pawn is looked at before taking a pawn with a queen.

At depth 0 the engine keeps searching captures, up to 8 more plies, until the position is quiet. Without that it would stop in the middle of an exchange and evaluate a position where a queen is about to be lost.

The transposition table is a dict keyed on the first four FEN fields (pieces, side to move, castling rights and en passant square). Each entry stores the depth, score, a bound flag (`EXACT`, `LOWER` or `UPPER`) and the best move. FEN keys are slower than Zobrist hashing, but they were easier to get right and to debug.

Evaluation is material plus piece-square tables, mirrored for Black. It handles checkmate, stalemate and insufficient material, and gives a small penalty for repeating a position. The evaluation is deliberately simple because the search was the part I wanted to learn.

## Measured behavior

- Iterative deepening stops at depth 6, which it doesn't reach in practice. Fixed-depth mode defaults to depth 3.
- On an M2, middlegame positions finish depth 3 in about 0.7 to 2 seconds and depth 4 in 4 to 14 seconds (cold transposition table, five positions). With a 0.5 to 1.5 second budget per move, the timed search reaches depth 2 or 3.
- The demo above is the engine playing Stockfish 15.1 in Banksia on a 1-minute clock. It has no opening book or endgame tables and it won't beat Stockfish. I haven't measured its Elo.

## Known issues

- When the transposition table has no move for a position, `ordered_moves` keeps the first legal move in front and only sorts the rest.
- The root search doesn't store its best move in the table, so the next depth doesn't try the previous best move first.
- `ucinewgame` resets the board but doesn't clear the transposition table.
- If time runs out during depth 1, the board is left with a move still pushed, and the fallback picks its move from that board.
- There are no tests yet.

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

The engine supports `uci`, `isready`, `ucinewgame`, `position startpos|fen ... moves ...`, `go depth N`, `go movetime <ms>` and clock mode with `go wtime/btime [winc/binc]`. When a clock is given it takes precedence over depth.

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
```

## Requirements

Python 3.10 or newer and [python-chess](https://python-chess.readthedocs.io/), which handles the board, legal move generation and FEN. Search, evaluation, move ordering and the UCI layer live in this repo.

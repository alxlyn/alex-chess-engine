# Alex Chess Engine

A UCI compatible chess engine written in python, implementing alpha-beta search with iterative deepening, quiescence search, and a transposition table.

## Features
-Alpha-beta pruning (Negamax framework)

-Iterative deepening

-Deadline-based time management

-Quiescence search (capture extension)

-Transposition table

-Basic move ordering (captures + checks + TT move)

-UCI protocol support (works in Banksia GUI and other UCI GUIs)

## Quick Start
# Clone Repo
git clone https://github.com/yourusername/alex-chess-engine.git
cd alex-chess-engine

# Virtual Environment and Dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run Engine Directly
python uci.py

# Run in GUI (supports Banksia, Arena, etc)
1. Open your chess GUI
2. Add a new UCI engine
3. Select run_engine.sh (or uci.py)
4. Start a game

# The engine supports:
go depth N
go movetime X
go wtime/btime

## Project Structure
engine/
  search.py        # Alpha-beta, quiescence, TT, move ordering
  evaluation.py    # Static evaluation
uci.py             # UCI protocol loop
run_engine.sh      # GUI launcher script

## Known Limitations
1. Not optimized for maximum speed
2. No position evalutation, purely material based
3. No opening book, endgame strategies
4. No advanced move heuristic


# Alex Chess Engine
Built as a personal systems project to deepen understanding of search algorithms and game AI.

A UCI compatible chess engine written in python, implementing alpha-beta search with iterative deepening, quiescence search, and a transposition table.

## Demo

![Engine Demo](assets/demo.gif)

## Project Summary

This project implements a UCI-compatible chess engine in Python,
featuring alpha-beta pruning, iterative deepening, quiescence search,
and a transposition table. The engine integrates with standard chess GUIs
and supports real-time time management.

The focus of this project was implementing core search algorithms
from scratch and building a working engine architecture.

## Performance

- Depth 5–6 in ~0.5–1.5 seconds (midgame)
- Iterative deepening with deadline-based cutoff
- Runs entirely in Python
- Uses transposition table for repeated position caching


## Design Decisions

- Used negamax framework for cleaner alpha-beta implementation.
- Implemented quiescence search to reduce horizon effect.
- Used FEN-based transposition keys for simplicity over performance.
- Prioritized clarity and correctness over micro-optimization.

## Features
- Alpha-beta pruning (Negamax framework)
- Iterative deepening
- Deadline-based time management
- Quiescence search (capture extension)
- Transposition table
- Basic move ordering (captures + checks + TT move)
- UCI protocol support (works in Banksia GUI and other UCI GUIs)

## Quick Start
# Clone Repo
- git clone https://github.com/alxlyn/alex-chess-engine.git
- cd alex-chess-engine

# Virtual Environment and Dependencies
- python3 -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt

# Run Engine Directly
- python uci.py

# Run in GUI (supports Banksia, Arena, etc)
1. Open your chess GUI
2. Add a new UCI engine
3. Select run_engine.sh (or uci.py)
4. Start a game

# The engine supports:
- go depth N
- go movetime X
- go wtime/btime

## Project Structure
- engine/
-   search.py        # Alpha-beta, quiescence, TT, move ordering
-   evaluation.py    # Static evaluation
- uci.py             # UCI protocol loop
- run_engine.sh      # GUI launcher script

## Known Limitations
1. Not optimized for maximum speed
2. No position evalutation, purely material based
3. No opening book, endgame strategies
4. No advanced move heuristic

## What I learned
- Search complexity grows exponentially — even small depth increases dramatically expand the search tree. Efficient pruning and move ordering are critical.
- The horizon effect is real — stopping search at a fixed depth can produce misleading evaluations. Quiescence search helps stabilize leaf evaluations in tactical positions.
- Time management is non-trivial — implementing deadline-based search required handling partial searches safely and ensuring the engine always returns a move.
- Caching matters — transposition tables significantly reduce repeated computation in complex positions.
- Correctness vs. performance tradeoffs — prioritizing clarity (e.g., FEN-based keys) simplifies implementation but impacts speed, highlighting real-world engineering decisions.

## Requirements

- Python 3.10+
- python-chess

# Alex Chess Engine

A simple chess engine in Python using python-chess, with alpha-beta (negamax) search and a basic evaluation.

## Features
- Legal move generation via python-chess
- Material-based evaluation
- Negamax + alpha-beta pruning
- UCI interface (can be run in chess GUIs)

## Run
Create venv and install:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copilot instructions for contributors and AI agents

This repository is a minimal chess engine project. Use these notes to get productive quickly.

- Purpose: implement a UCI-capable chess engine split between a CLI/UCI layer and an `engine` package.

**Repository layout**
- Entry: [main.py](main.py) — top-level runner (currently placeholder).
- UCI interface: [uci.py](uci.py) — where UCI command handling and loop belong.
- Engine implementation: [engine/search.py](engine/search.py) and [engine/evalutation.py](engine/evalutation.py) — search and evaluation logic live here. Note: `evalutation.py` is intentionally misspelled in the tree; keep the filename when importing.
- Dependencies: [requirements.txt](requirements.txt) — uses `chess` / `python-chess` libraries.

**Big-picture architecture (what to expect and preserve)**
- The project separates concerns: UCI/CLI (I/O) vs engine logic (search + evaluation). Keep I/O code in `uci.py` and pure engine algorithms in `engine/` so the engine can be imported and tested independently.
- Data flow: UCI loop receives moves / position (FEN) and forwards board state to engine.search.* functions; engine returns a best-move string (UCI format) and optional ponder info.
- External dependency: `python-chess` (or `chess`) is used for board representation and move generation — rely on its Board and Move objects rather than reimplementing them.

**Project-specific conventions**
- File-level separation: heavy algorithmic code goes in `engine/`; small glue or CLI pieces stay at repository root.
- Filename caution: keep `engine/evalutation.py` name (typo) if you reference existing imports; rename only if you update all imports and document the change.
- Imports: prefer `from engine import search` (package-level imports) to keep tests and CLI usage simple.

**Developer workflows (commands you can run now)**
- Install deps: `python -m pip install -r requirements.txt`.
- Quick run (manual testing): `python main.py` or `python uci.py` — these are the user-facing launchers; open them to see expected arguments or to wire UCI loop.
- Debugging: run the same commands with `-m pdb` or use editor breakpoints. Since there are no tests yet, iterate locally by importing engine modules in a REPL:
  - `python -c "from engine import search; print(search)"`

**Integration points and patterns to follow when editing**
- When adding search routines, accept and return python-chess objects or UCI-compatible strings so `uci.py` can remain minimal.
- Keep pure logic (evaluation, move ordering, pruning) in `engine/` and avoid printing/logging from core functions; surface logging via `uci.py` or a small runner in `main.py`.

**Merging guidance for this file**
- If a `.github/copilot-instructions.md` already exists, preserve any project-specific notes and merge these sections under a "Repo-specific" header. Keep examples and filenames intact.

If any parts are unclear or you want more detail (example function signatures, preferred logging format, or a minimal test harness), tell me which area and I'll update this file.

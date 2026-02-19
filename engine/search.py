import math
import chess
import time

from engine.evaluation import evaluate_side_to_move

def ordered_moves(board: chess.Board):
    """
    Basic move ordering: captures first, then checks.
    Improves alpha-beta pruning a lot.
    """
    moves = list(board.legal_moves)

    def key(m: chess.Move):
        capture = 1 if board.is_capture(m) else 0
        board.push(m)
        gives_check = 1 if board.is_check() else 0
        board.pop()
        return (capture, gives_check)

    moves.sort(key=key, reverse=True)
    return moves

def negamax(board: chess.Board, depth: int, alpha: int, beta: int) -> int:
    if depth == 0 or board.is_game_over(claim_draw=True):
        return evaluate_side_to_move(board)

    best = -math.inf
    for move in ordered_moves(board):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha)
        board.pop()

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break  # beta cut-off

    return int(best)

def choose_move(board: chess.Board, depth: int = 3) -> chess.Move:
    best_move = None
    best_score = -math.inf
    alpha, beta = -10_000_000, 10_000_000

    for move in ordered_moves(board):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha)
        board.pop()

        if score > best_score:
            best_score = score
            best_move = move
        if best_score > alpha:
            alpha = best_score

    assert best_move is not None
    return best_move
def choose_move_timed(board: chess.Board, time_limit_s: float) -> chess.Move:
    """
    Iterative deepening: search depth 1,2,3... until time runs out.
    Returns the best move found so far.
    """
    start = time.time()
    best_move = None
    depth = 1

    while True:
        # Stop if out of time (leave a tiny buffer)
        if time.time() - start > time_limit_s * 0.97:
            break

        try:
            move = choose_move(board, depth=depth)
            best_move = move
            depth += 1
        except Exception:
            break

    # fallback if something weird happens
    if best_move is None:
        best_move = next(iter(board.legal_moves))
    return best_move
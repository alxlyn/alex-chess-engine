import math
import time
import chess

from engine.evaluation import evaluate_side_to_move

INF = 10_000_000


def ordered_moves(board: chess.Board):
    moves = list(board.legal_moves)

    def key(m: chess.Move):
        capture = 1 if board.is_capture(m) else 0
        board.push(m)
        gives_check = 1 if board.is_check() else 0
        board.pop()
        return (capture, gives_check)

    moves.sort(key=key, reverse=True)
    return moves


def quiescence(board: chess.Board, alpha: int, beta: int):
    stand_pat = evaluate_side_to_move(board)

    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    for move in board.legal_moves:
        if not board.is_capture(move):
            continue

        board.push(move)
        score = -quiescence(board, -beta, -alpha)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board: chess.Board, depth: int, alpha: int, beta: int):
    if board.is_game_over(claim_draw=True):
        return evaluate_side_to_move(board)

    if depth == 0:
        return quiescence(board, alpha, beta)

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
            break

    return int(best)


def choose_move(board: chess.Board, depth: int = 3):
    best_move = None
    best_score = -math.inf
    alpha, beta = -INF, INF

    for move in ordered_moves(board):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha)
        board.pop()

        if score > best_score:
            best_score = score
            best_move = move
        if best_score > alpha:
            alpha = best_score

    if best_move is None:
        best_move = next(iter(board.legal_moves))

    return best_move


def choose_move_timed(board: chess.Board, time_limit_s: float):
    start = time.time()
    best_move = None
    depth = 1

    while True:
        if time.time() - start > time_limit_s * 0.97:
            break

        move = choose_move(board, depth)
        best_move = move
        depth += 1

    if best_move is None:
        best_move = next(iter(board.legal_moves))

    return best_move

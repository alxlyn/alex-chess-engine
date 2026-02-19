import math
import time
import chess

from engine.evaluation import evaluate_side_to_move

INF = 10_000_000

# Transposition Table:
# key -> (depth, flag, value, best_move_uci)
# flag: "EXACT", "LOWER", "UPPER"
TT = {}


def tt_key(board: chess.Board):
    return board.fen()




def ordered_moves(board: chess.Board):
    moves = list(board.legal_moves)

    # If we have a stored best move for this position, try it first
    key = tt_key(board)
    entry = TT.get(key)
    if entry is not None:
        _, _, _, best_move_uci = entry
        if best_move_uci:
            try:
                bm = chess.Move.from_uci(best_move_uci)
                if bm in moves:
                    moves.remove(bm)
                    moves.insert(0, bm)
            except Exception:
                pass

    def sort_key(m: chess.Move):
        capture = 1 if board.is_capture(m) else 0
        board.push(m)
        gives_check = 1 if board.is_check() else 0
        board.pop()
        return (capture, gives_check)

    # Keep the TT move in front, sort the rest
    if len(moves) > 1:
        first = moves[0]
        rest = moves[1:]
        rest.sort(key=sort_key, reverse=True)
        moves = [first] + rest

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

    key = tt_key(board)
    alpha_orig = alpha
    beta_orig = beta

    # TT lookup
    entry = TT.get(key)
    if entry is not None:
        tt_depth, flag, val, _ = entry
        if tt_depth >= depth:
            if flag == "EXACT":
                return val
            elif flag == "LOWER":
                alpha = max(alpha, val)
            elif flag == "UPPER":
                beta = min(beta, val)
            if alpha >= beta:
                return val

    best = -math.inf
    best_move_uci = None

    for move in ordered_moves(board):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha)
        board.pop()

        if score > best:
            best = score
            best_move_uci = move.uci()

        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    best = int(best)

    # TT store
    if best <= alpha_orig:
        flag = "UPPER"
    elif best >= beta_orig:
        flag = "LOWER"
    else:
        flag = "EXACT"

    TT[key] = (depth, flag, best, best_move_uci)

    return best


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

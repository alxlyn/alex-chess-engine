import math
import time
import chess

from engine.evaluation import evaluate_side_to_move

INF = 10_000_000

# Transposition Table:
# key -> (depth, flag, value, best_move_uci)
# flag: "EXACT", "LOWER", "UPPER"
TT = {}
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

def tt_key(board: chess.Board):
    return tuple(board.fen().split(" ", 4)[:4])






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


def _capture_moves(board: chess.Board):
    """Return legal captures, roughly ordered (good captures first)."""
    moves = [m for m in board.legal_moves if board.is_capture(m)]

    def mvv_lva_key(m: chess.Move):
        victim = board.piece_at(m.to_square)
        attacker = board.piece_at(m.from_square)
        v = PIECE_VALUES.get(victim.piece_type, 0) if victim else 0
        a = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0
        # bigger victim and smaller attacker first
        return (v * 100 - a)

    moves.sort(key=mvv_lva_key, reverse=True)
    return moves

def quiescence(board: chess.Board, alpha: int, beta: int, qdepth: int = 0) -> int:
    """
    Quiescence search: only explore tactical moves (captures) at the leaf.
    Adds a hard depth cap so it can't explode forever.
    """
    stand_pat = evaluate_side_to_move(board)

    # Hard stop to prevent infinite recursion in crazy positions (e.g. perpetual check)
    if qdepth >= 8:
        return stand_pat

    # Fail-hard beta cutoff if the static eval is already too good for the side to move
    if stand_pat >= beta:
        return beta

    # Improve alpha with static eval if it's better than current alpha
    if stand_pat > alpha:
        alpha = stand_pat

    # Explore captures only 
    for move in _capture_moves(board):
        board.push(move)
        score = -quiescence(board, -beta, -alpha, qdepth + 1)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha



def negamax(board: chess.Board, depth: int, alpha: int, beta: int, deadline=None):
    if deadline is not None and time.time() >= deadline:
        raise TimeoutError

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
        score = -negamax(board, depth - 1, -beta, -alpha, deadline)
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


def choose_move(board: chess.Board, depth: int = 3, deadline=None):
    best_move = None
    best_score = -math.inf
    alpha, beta = -INF, INF

    for move in ordered_moves(board):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, deadline)
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
    deadline = time.time() + time_limit_s * 0.97
    best_move = None
    depth = 1

    while True:
        if time.time() >= deadline:
            break
        if depth > 6:
            break

        try:
            move = choose_move(board, depth=depth, deadline=deadline)
            best_move = move
            depth += 1
        except TimeoutError:
            break

    if best_move is None:
        best_move = next(iter(board.legal_moves))

    return best_move


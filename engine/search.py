import math
import time
import chess

from engine.evaluation import evaluate_side_to_move
# Negamax search with alpha-beta pruning and a transposition table.
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
# PSTs are defined in evaluation.py, but we need them here for move ordering.
def tt_key(board: chess.Board):
    return tuple(board.fen().split(" ", 4)[:4])





# Move ordering: try TT move first, then captures and checks, ordered by MVV/LVA.
def ordered_moves(board: chess.Board):
    moves = list(board.legal_moves)

    # Move ordering is a huge deal for alpha-beta pruning efficiency. We want to try the most promising moves first to maximize cutoffs.
    key = tt_key(board)
    entry = TT.get(key)
    # If we have a TT entry with a best move, try it first. This is often the best move from the previous search at this position, so it's a great heuristic.
    if entry is not None:
        _, _, _, best_move_uci = entry
        if best_move_uci:
            # Move the TT best move to the front of the list if it's legal. This can lead to much faster alpha-beta cutoffs.
            try:
                bm = chess.Move.from_uci(best_move_uci)
                if bm in moves:
                    moves.remove(bm)
                    moves.insert(0, bm)
            except Exception:
                pass
    # After the TT move, we sort captures and checks to try the most promising ones first. This is a common heuristic to improve pruning.            
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

# MVV/LVA sorting for captures: Most Valuable Victim / Least Valuable Attacker. 
# This is a common heuristic to order captures, trying the most "valuable" ones first 
# (e.g. capturing a queen with a pawn is usually better than capturing a pawn with a queen).
def _capture_moves(board: chess.Board):
    moves = [m for m in board.legal_moves if board.is_capture(m)]
    # We sort captures by MVV/LVA: capture the most valuable victim with the least valuable attacker first. This often leads to better pruning in quiescence search.
    def mvv_lva_key(m: chess.Move):
        victim = board.piece_at(m.to_square)
        attacker = board.piece_at(m.from_square)
        v = PIECE_VALUES.get(victim.piece_type, 0) if victim else 0
        a = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0
        return (v * 100 - a)

    moves.sort(key=mvv_lva_key, reverse=True)
    return moves

# Quiescence search: extends the search at leaf nodes to include captures,
# to avoid the "horizon effect" where the engine misses a tactical sequence just beyond the search depth.
def quiescence(board: chess.Board, alpha: int, beta: int, qdepth: int = 0) -> int:

    stand_pat = evaluate_side_to_move(board)
    # Hard limit on quiescence depth to prevent infinite recursion in crazy positions. 
    if qdepth >= 8:
        return stand_pat

    # If the static evaluation is already good enough to cause a beta cutoff, we can stop searching this branch. This is a key part of alpha-beta pruning.
    if stand_pat >= beta:
        return beta

    # If the static evaluation is better than alpha, we update alpha.
    if stand_pat > alpha:
        alpha = stand_pat

    # Now we try all captures from this position. This is the "quiescence" part.
    for move in _capture_moves(board):
        board.push(move)
        score = -quiescence(board, -beta, -alpha, qdepth + 1)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


# Negamax search with alpha-beta pruning and a transposition table. Returns the score from the perspective of the side to move.
def negamax(board: chess.Board, depth: int, alpha: int, beta: int, deadline=None):
    # Check for timeout at the start of each node. This allows us to gracefully exit the search when we run out of time, returning the best move found so far.
    if deadline is not None and time.time() >= deadline:
        raise TimeoutError
    # If the game is already over, return the evaluation. This is a terminal node in the search tree.
    if board.is_game_over(claim_draw=True):
        return evaluate_side_to_move(board)
    # If we've reached the maximum search depth, we switch to quiescence search to evaluate the position more accurately.
    if depth == 0:
        return quiescence(board, alpha, beta)

    key = tt_key(board)
    alpha_orig = alpha
    beta_orig = beta

    # Check the transposition table to see if we've already evaluated this position at an equal or greater depth (TIME SAVER).
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
    # Move ordering is crucial for alpha-beta efficiency. We want to try the most promising moves first to maximize cutoffs. 
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

    # Store the result in the transposition table. This allows us to reuse this information if we encounter the same position again at an equal or shallower depth.
    if best <= alpha_orig:
        flag = "UPPER"
    elif best >= beta_orig:
        flag = "LOWER"
    else:
        flag = "EXACT"

    TT[key] = (depth, flag, best, best_move_uci)

    return best

# Top-level function to choose the best move from a given position and search depth.
def choose_move(board: chess.Board, depth: int = 3, deadline=None):
    best_move = None
    best_score = -math.inf
    alpha, beta = -INF, INF
    # Move ordering is crucial for alpha-beta efficiency. We want to try the most promising moves first to maximize cutoffs.
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
# Iterative deepening with a time limit. We keep deepening the search until we run out of time.
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


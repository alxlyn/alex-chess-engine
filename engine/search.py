import math
import time
import chess

from engine.evaluation import evaluate_side_to_move
# Negamax search with alpha-beta pruning and a transposition table.
INF = 10_000_000
# The search reads time through this name, so tests can swap in a fake clock.
clock = time.monotonic
# A mate scores MATE minus the plies it takes, so a faster mate is worth more.
MATE = 100_000
MATE_BOUND = MATE - 1_000  # anything above this is a mate score

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


# Mate scores count plies from the root, but the same position can come up at a
# different ply, so the table stores them relative to the node instead.
def to_tt(score: int, ply: int) -> int:
    if score > MATE_BOUND:
        return score + ply
    if score < -MATE_BOUND:
        return score - ply
    return score


def from_tt(score: int, ply: int) -> int:
    if score > MATE_BOUND:
        return score - ply
    if score < -MATE_BOUND:
        return score + ply
    return score


def tt_key(board: chess.Board):
    return tuple(board.fen().split(" ", 4)[:4])

# Move ordering: the table's best move first, then captures, then checks.
def ordered_moves(board: chess.Board):
    entry = TT.get(tt_key(board))
    tt_move = chess.Move.from_uci(entry[3]) if entry and entry[3] else None

    def sort_key(m: chess.Move):
        return (m == tt_move, board.is_capture(m), board.gives_check(m))

    return sorted(board.legal_moves, key=sort_key, reverse=True)

# MVV/LVA capture ordering
# Biggest victim first, cheapest attacker first (pawn takes queen before queen takes pawn).
def _capture_moves(board: chess.Board):
    moves = list(board.generate_legal_captures())  # only captures, not every legal move
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
def quiescence(board: chess.Board, alpha: int, beta: int, qdepth: int = 0, deadline=None, ply: int = 0) -> int:
    if deadline is not None and clock() >= deadline:
        raise TimeoutError
    if board.is_checkmate():  # cheap unless in check
        return -(MATE - ply)  # a mate found by a capture is scored by distance too
    stand_pat = evaluate_side_to_move(board)

    # Hard limit on quiescence depth to prevent infinite recursion in crazy positions. 
    if qdepth >= 8:
        return stand_pat
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    #This is the "quiescence" part.
    for move in _capture_moves(board):
        board.push(move)
        score = -quiescence(board, -beta, -alpha, qdepth + 1, deadline, ply + 1)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


# Negamax search with alpha-beta pruning and a transposition table. Returns the score from the perspective of the side to move.
def negamax(board: chess.Board, depth: int, alpha: int, beta: int, deadline=None, ply: int = 1):
    if deadline is not None and clock() >= deadline:
        raise TimeoutError
    # No legal moves: checkmate if in check, otherwise stalemate.
    if not any(board.generate_legal_moves()):
        return -(MATE - ply) if board.is_check() else 0
    # Draws. A repeated position is scored as a draw here, before the table is read or
    # written, because the table key has no move history. These checks are cheap;
    # can_claim_draw() tried every legal move at every node and ate most of the time.
    if board.is_repetition(2) or board.halfmove_clock >= 100 or board.is_insufficient_material():
        return 0
    if depth <= 0:
        return quiescence(board, alpha, beta, 0, deadline, ply)

    key = tt_key(board)
    alpha_orig = alpha
    beta_orig = beta

    # Check the transposition table to see if we've already evaluated this position at an equal or greater depth (TIME SAVER).
    entry = TT.get(key)
    if entry is not None:
        tt_depth, flag, val, _ = entry
        val = from_tt(val, ply)
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

    # Better moves first means more cutoffs.
    for move in ordered_moves(board):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, deadline, ply + 1)
        board.pop()

        if score > best:
            best = score
            best_move_uci = move.uci()

        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    best = int(best)

    # Store the result in the transposition table. 
    if best <= alpha_orig:
        flag = "UPPER"
    elif best >= beta_orig:
        flag = "LOWER"
    else:
        flag = "EXACT"

    TT[key] = (depth, flag, to_tt(best, ply), best_move_uci)

    return best

class SearchTimeout(TimeoutError):
    """The deadline passed during a search. Carries the best root move found so far, if any."""

    def __init__(self, best_move=None):
        super().__init__()
        self.best_move = best_move


# Top-level function to choose the best move from a given position and search depth.
# It searches a copy, so a timeout can never leave moves pushed on the caller's board.
def choose_move(board: chess.Board, depth: int = 3, deadline=None):
    board = board.copy()
    best_move = None
    best_score = -math.inf
    alpha, beta = -INF, INF
    for move in ordered_moves(board):
        board.push(move)
        try:
            score = -negamax(board, depth - 1, -beta, -alpha, deadline)
        except TimeoutError:
            raise SearchTimeout(best_move) from None
        board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        if best_score > alpha:
            alpha = best_score

    # Keep the root's best move so the next, deeper search tries it first.
    if best_move is not None:
        TT[tt_key(board)] = (depth, "EXACT", int(best_score), best_move.uci())
    return best_move


# Iterative deepening with a time limit: search depth 1, 2, 3... and keep the move
# from the deepest search that finished.
def choose_move_timed(board: chess.Board, time_limit_s: float):
    deadline = clock() + time_limit_s * 0.97
    moves = ordered_moves(board)
    best_move = moves[0] if moves else None  # something legal even if depth 1 never finishes
    for depth in range(1, 7):
        try:
            best_move = choose_move(board, depth=depth, deadline=deadline)
        except SearchTimeout as timeout:
            # A half-finished depth 1 still beats a blind guess.
            if depth == 1 and timeout.best_move is not None:
                best_move = timeout.best_move
            break
        if clock() >= deadline:
            break

    return best_move



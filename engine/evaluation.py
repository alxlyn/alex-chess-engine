import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

def evaluate_white(board: chess.Board) -> int:
    """
    Evaluation from White's perspective:
    positive = good for White, negative = good for Black.
    """
    # Terminal positions
    if board.is_checkmate():
        # side to move is checkmated
        return -10_000 if board.turn == chess.WHITE else 10_000

    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0

    score = 0
    for pt, val in PIECE_VALUES.items():
        score += len(board.pieces(pt, chess.WHITE)) * val
        score -= len(board.pieces(pt, chess.BLACK)) * val
    return score

def evaluate_side_to_move(board: chess.Board) -> int:
    """
    Convert White-perspective score to the current side-to-move perspective.
    positive = good for the player to move.
    """
    base = evaluate_white(board)
    return base if board.turn == chess.WHITE else -base

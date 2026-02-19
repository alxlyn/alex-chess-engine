import chess
from engine.search import choose_move

def self_play(plies: int = 60, depth: int = 3):
    board = chess.Board()
    for i in range(plies):
        if board.is_game_over(claim_draw=True):
            break
        move = choose_move(board, depth=depth)
        board.push(move)
        print(f"{i+1:02d}. {move.uci()}")

    print("Result:", board.result(claim_draw=True))
    print(board)

if __name__ == "__main__":
    self_play(plies=80, depth=3)

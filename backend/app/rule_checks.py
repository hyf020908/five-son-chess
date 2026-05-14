from __future__ import annotations

from .config import BLACK
from .game_engine import GameRuleError, apply_move, check_draw, check_winner, empty_board


def _assert_winner(coords: list[tuple[int, int]]) -> None:
    board = empty_board()
    for row, col in coords:
        board[row][col] = BLACK
    assert check_winner(board) == BLACK


def run_rule_checks() -> None:
    _assert_winner([(7, 3), (7, 4), (7, 5), (7, 6), (7, 7)])
    _assert_winner([(3, 7), (4, 7), (5, 7), (6, 7), (7, 7)])
    _assert_winner([(3, 3), (4, 4), (5, 5), (6, 6), (7, 7)])
    _assert_winner([(7, 3), (6, 4), (5, 5), (4, 6), (3, 7)])

    board = empty_board()
    board = apply_move(board, 7, 7, BLACK)
    try:
      apply_move(board, 7, 7, BLACK)
    except GameRuleError:
      pass
    else:
      raise AssertionError("Repeated move should be rejected.")

    draw_board = [
        [BLACK if ((row + 2 * col) % 5) < 2 else 2 for col in range(15)]
        for row in range(15)
    ]
    assert check_draw(draw_board)


if __name__ == "__main__":
    run_rule_checks()
    print("Rule checks passed.")

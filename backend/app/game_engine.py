from __future__ import annotations

from copy import deepcopy
from typing import Optional

from .config import BLACK, BOARD_SIZE, EMPTY, WHITE
from .models import GameStatus, Move

DIRECTIONS: tuple[tuple[int, int], ...] = ((1, 0), (0, 1), (1, 1), (1, -1))


class GameRuleError(ValueError):
    """Raised when a board or move violates Gomoku rules."""


def validate_board(board: list[list[int]]) -> None:
    if len(board) != BOARD_SIZE:
        raise GameRuleError(f"Board must have {BOARD_SIZE} rows.")
    for row in board:
        if len(row) != BOARD_SIZE:
            raise GameRuleError(f"Board must have {BOARD_SIZE} columns.")
        if any(cell not in (EMPTY, BLACK, WHITE) for cell in row):
            raise GameRuleError("Board contains an invalid cell value.")


def is_in_bounds(row: int, col: int) -> bool:
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def validate_move(board: list[list[int]], row: int, col: int, player: int) -> None:
    validate_board(board)
    if player not in (BLACK, WHITE):
        raise GameRuleError("Player must be 1 or 2.")
    if not is_in_bounds(row, col):
        raise GameRuleError("Move is outside the board.")
    if board[row][col] != EMPTY:
        raise GameRuleError("Move target is already occupied.")
    if check_winner(board) is not None:
        raise GameRuleError("The game is already finished.")


def apply_move(board: list[list[int]], row: int, col: int, player: int) -> list[list[int]]:
    validate_move(board, row, col, player)
    next_board = deepcopy(board)
    next_board[row][col] = player
    return next_board


def count_line(board: list[list[int]], row: int, col: int, player: int, dr: int, dc: int) -> int:
    count = 0
    r, c = row + dr, col + dc
    while is_in_bounds(r, c) and board[r][c] == player:
        count += 1
        r += dr
        c += dc
    return count


def line_length_after_move(board: list[list[int]], row: int, col: int, player: int, dr: int, dc: int) -> int:
    return 1 + count_line(board, row, col, player, dr, dc) + count_line(board, row, col, player, -dr, -dc)


def check_winner(board: list[list[int]]) -> Optional[int]:
    validate_board(board)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            player = board[row][col]
            if player == EMPTY:
                continue
            for dr, dc in DIRECTIONS:
                if count_line(board, row, col, player, dr, dc) >= 4:
                    return player
    return None


def check_draw(board: list[list[int]]) -> bool:
    validate_board(board)
    return check_winner(board) is None and all(cell != EMPTY for row in board for cell in row)


def get_status(board: list[list[int]]) -> tuple[GameStatus, Optional[int]]:
    winner = check_winner(board)
    if winner == BLACK:
        return "black_win", BLACK
    if winner == WHITE:
        return "white_win", WHITE
    if check_draw(board):
        return "draw", None
    return "ongoing", None


def get_legal_moves(board: list[list[int]]) -> list[tuple[int, int]]:
    validate_board(board)
    if check_winner(board) is not None:
        return []
    return [(row, col) for row in range(BOARD_SIZE) for col in range(BOARD_SIZE) if board[row][col] == EMPTY]


def serialize_board_for_prompt(board: list[list[int]]) -> str:
    validate_board(board)
    symbols = {EMPTY: "0", BLACK: "B", WHITE: "W"}
    header = "    " + " ".join(f"{col:02d}" for col in range(BOARD_SIZE))
    lines = [header]
    for row_index, row in enumerate(board):
        values = " ".join(symbols[cell] for cell in row)
        lines.append(f"{row_index:02d}  {values}")
    return "\n".join(lines)


def get_move_history_text(move_history: list[Move], limit: int = 12) -> str:
    if not move_history:
        return "No moves have been played."
    recent = move_history[-limit:]
    lines = []
    offset = len(move_history) - len(recent)
    for index, move in enumerate(recent, start=offset + 1):
        player = "Black" if move.player == BLACK else "White"
        lines.append(f"{index}. {player} at row {move.row}, col {move.col}")
    return "\n".join(lines)


def empty_board() -> list[list[int]]:
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

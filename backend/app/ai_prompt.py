from __future__ import annotations

from typing import Optional

from .config import BLACK, WHITE
from .game_engine import get_legal_moves, get_move_history_text, serialize_board_for_prompt
from .models import Move


def build_ai_messages(
    board: list[list[int]],
    move_history: list[Move],
    ai_player: int = WHITE,
    last_error: Optional[str] = None,
) -> list[dict[str, str]]:
    ai_color = "Black" if ai_player == BLACK else "White"
    opponent_color = "White" if ai_player == BLACK else "Black"
    legal_moves = get_legal_moves(board)
    legal_move_text = ", ".join(f"({row}, {col})" for row, col in legal_moves)

    error_section = (
        f"\nPrevious response error: {last_error}\nReturn a corrected legal JSON move."
        if last_error
        else ""
    )
    user_content = f"""
Board size: 15 x 15.
Coordinates are zero-based integers. Use row 0..14 and col 0..14.
{ai_color} is the AI player. {opponent_color} is the opponent. It is {ai_color}'s turn.

Board:
{serialize_board_for_prompt(board)}

Recent move history:
{get_move_history_text(move_history)}

Legal empty coordinates:
{legal_move_text}
{error_section}

Choose exactly one legal empty coordinate. Use only your own Gomoku analysis. No pre-ranked candidate list or deterministic strategy suggestion is provided.
""".strip()

    system_content = """
You are playing fair Gomoku as the AI player.
Rules: five or more consecutive stones horizontally, vertically, or diagonally wins. Occupied cells are illegal. The game state has no hidden information.
You must choose the move only from the visible board state and the legal coordinate list. The application will not provide heuristic move choices, automatic wins, forced blocks, ranked candidates, or fallback moves.

Return strict JSON only, with this shape:
{"row": 7, "col": 8, "reason": "This move creates the strongest threat while reducing the opponent's options."}

Do not return Markdown. Do not use a code block. Do not include extra text.
""".strip()

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

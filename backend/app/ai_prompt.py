from __future__ import annotations

from typing import Optional

from .config import BLACK, WHITE
from .game_engine import get_move_history_text, serialize_board_for_prompt
from .models import Move


def build_ai_messages(
    board: list[list[int]],
    move_history: list[Move],
    ai_player: int = WHITE,
    last_error: Optional[str] = None,
) -> list[dict[str, str]]:
    ai_color = "Black" if ai_player == BLACK else "White"
    opponent_color = "White" if ai_player == BLACK else "Black"

    error_section = (
        f"\nPrevious response error: {last_error}\nReturn a corrected legal JSON move with row and col only. The coordinate must point to a 0 cell."
        if last_error
        else ""
    )
    user_content = f"""
Board size: 15 x 15.
Coordinates are zero-based integers. Use row 0..14 and col 0..14.
{ai_color} is the AI player. {opponent_color} is the opponent. It is {ai_color}'s turn.
Cell legend: 0 = empty legal cell, B = Black stone, W = White stone.
You may place a stone only on a 0 cell. You must not choose a B or W cell.

Board:
{serialize_board_for_prompt(board)}

Recent move history:
{get_move_history_text(move_history)}
{error_section}

Choose exactly one empty coordinate from the matrix. Use only your own Gomoku analysis. No pre-ranked candidate list or deterministic strategy suggestion is provided.
""".strip()

    system_content = """
You are playing fair Gomoku as the AI player.
Rules: five or more consecutive stones horizontally, vertically, or diagonally wins. Occupied cells are illegal. The game state has no hidden information.
The board is provided as a fixed matrix. In the matrix, 0 means an empty legal cell, B means a Black stone, and W means a White stone. You must choose a coordinate whose matrix value is 0.
The application will not provide heuristic move choices, automatic wins, forced blocks, ranked candidates, legal-coordinate lists, or fallback moves.

Return strict JSON only, with this exact shape:
{"row": 7, "col": 8}

Do not include any other keys. Do not return Markdown. Do not use a code block. Do not include extra text.
""".strip()

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

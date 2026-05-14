from __future__ import annotations

from typing import Optional

from .config import BLACK, WHITE
from .game_engine import get_move_history_text, serialize_board_for_prompt
from .models import Move
from .ai_strategy import StrategyReport


def build_ai_messages(
    board: list[list[int]],
    move_history: list[Move],
    report: StrategyReport,
    ai_player: int = WHITE,
    last_error: Optional[str] = None,
) -> list[dict[str, str]]:
    ai_color = "Black" if ai_player == BLACK else "White"
    opponent_color = "White" if ai_player == BLACK else "Black"
    candidate_lines = []
    for candidate in report.candidates:
        tags = ", ".join(candidate.tags) if candidate.tags else "positional"
        candidate_lines.append(
            f"- row {candidate.row}, col {candidate.col}: score {candidate.score}; tags: {tags}; reason: {candidate.reason}"
        )

    error_section = f"\nPrevious response error: {last_error}\nReturn a corrected legal JSON move." if last_error else ""
    user_content = f"""
Board size: 15 x 15.
Coordinates are zero-based integers. Use row 0..14 and col 0..14.
{ai_color} is the AI player. {opponent_color} is the opponent. It is {ai_color}'s turn.

Board:
{serialize_board_for_prompt(board)}

Recent move history:
{get_move_history_text(move_history)}

Position analysis:
{report.brief_analysis}

Candidate moves:
{chr(10).join(candidate_lines)}
{error_section}

Select exactly one legal move from the candidate list unless a listed immediate win or forced block is present.
""".strip()

    system_content = """
You are playing fair Gomoku as the AI player.
Rules: five or more consecutive stones horizontally, vertically, or diagonally wins. Occupied cells are illegal. The game state has no hidden information.
Decision priority:
1. Play an immediate winning move for your color.
2. Block the opponent's immediate winning move.
3. Create strong threats such as open fours, closed fours, and open threes.
4. Block the opponent's strongest threats.
5. Extend useful lines near existing stones and avoid unrelated distant moves.

Return strict JSON only, with this shape:
{"row": 7, "col": 8, "reason": "Blocks the opponent's strongest extension while creating a threat."}

Do not return Markdown. Do not use a code block. Do not include extra text.
""".strip()

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

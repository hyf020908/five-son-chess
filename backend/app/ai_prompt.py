from __future__ import annotations

from typing import Optional

from .game_engine import get_move_history_text, serialize_board_for_prompt
from .models import Move
from .ai_strategy import StrategyReport


def build_ai_messages(board: list[list[int]], move_history: list[Move], report: StrategyReport, last_error: Optional[str] = None) -> list[dict[str, str]]:
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
Black is the human player. White is the AI. It is White's turn.

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
You are playing fair Gomoku as White against a human Black player.
Rules: five or more consecutive stones horizontally, vertically, or diagonally wins. Occupied cells are illegal. The game state has no hidden information.
Decision priority:
1. Play an immediate winning move for White.
2. Block Black's immediate winning move.
3. Create strong threats such as open fours, closed fours, and open threes.
4. Block Black's strongest threats.
5. Extend useful White lines near existing stones and avoid unrelated distant moves.

Return strict JSON only, with this shape:
{"row": 7, "col": 8, "reason": "Blocks Black's strongest extension while creating a White threat."}

Do not return Markdown. Do not use a code block. Do not include extra text.
""".strip()

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

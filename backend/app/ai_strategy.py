from __future__ import annotations

from dataclasses import dataclass, field

from .config import BLACK, BOARD_SIZE, EMPTY, WHITE
from .game_engine import DIRECTIONS, apply_move, check_winner, get_legal_moves, is_in_bounds, line_length_after_move


@dataclass
class CandidateMove:
    row: int
    col: int
    score: int
    tags: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class StrategyReport:
    immediate_wins: list[CandidateMove]
    opponent_immediate_wins: list[CandidateMove]
    candidates: list[CandidateMove]
    brief_analysis: str


def _distance_to_center(row: int, col: int) -> int:
    center = BOARD_SIZE // 2
    return abs(row - center) + abs(col - center)


def _neighbor_count(board: list[list[int]], row: int, col: int, radius: int = 2) -> int:
    count = 0
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            if dr == 0 and dc == 0:
                continue
            r, c = row + dr, col + dc
            if is_in_bounds(r, c) and board[r][c] != EMPTY:
                count += 1
    return count


def _has_any_stone(board: list[list[int]]) -> bool:
    return any(cell != EMPTY for row in board for cell in row)


def _line_shape(board: list[list[int]], row: int, col: int, player: int, dr: int, dc: int) -> tuple[int, int]:
    total = line_length_after_move(board, row, col, player, dr, dc)
    open_ends = 0

    r, c = row + dr, col + dc
    while is_in_bounds(r, c) and board[r][c] == player:
        r += dr
        c += dc
    if is_in_bounds(r, c) and board[r][c] == EMPTY:
        open_ends += 1

    r, c = row - dr, col - dc
    while is_in_bounds(r, c) and board[r][c] == player:
        r -= dr
        c -= dc
    if is_in_bounds(r, c) and board[r][c] == EMPTY:
        open_ends += 1

    return total, open_ends


def _score_for_player(board: list[list[int]], row: int, col: int, player: int, prefix: str) -> tuple[int, list[str]]:
    score = 0
    tags: list[str] = []
    best_length = 0

    for dr, dc in DIRECTIONS:
        length, open_ends = _line_shape(board, row, col, player, dr, dc)
        best_length = max(best_length, length)
        if length >= 5:
            score += 1_000_000
            tags.append(f"{prefix}_immediate_win")
        elif length == 4 and open_ends == 2:
            score += 80_000
            tags.append(f"{prefix}_open_four")
        elif length == 4 and open_ends == 1:
            score += 30_000
            tags.append(f"{prefix}_closed_four")
        elif length == 3 and open_ends == 2:
            score += 8_000
            tags.append(f"{prefix}_open_three")
        elif length == 3 and open_ends == 1:
            score += 1_600
            tags.append(f"{prefix}_closed_three")
        elif length == 2 and open_ends == 2:
            score += 700
            tags.append(f"{prefix}_open_two")

    if best_length >= 2:
        tags.append("extend_line")
        score += best_length * 120

    return score, tags


def _candidate_pool(board: list[list[int]]) -> set[tuple[int, int]]:
    legal = set(get_legal_moves(board))
    if not legal:
        return set()
    if not _has_any_stone(board):
        center = BOARD_SIZE // 2
        return {(center, center)}

    pool: set[tuple[int, int]] = set()
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == EMPTY:
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    r, c = row + dr, col + dc
                    if is_in_bounds(r, c) and board[r][c] == EMPTY:
                        pool.add((r, c))
    return pool & legal


def _find_immediate_wins(board: list[list[int]], player: int) -> list[CandidateMove]:
    moves: list[CandidateMove] = []
    for row, col in get_legal_moves(board):
        next_board = apply_move(board, row, col, player)
        if check_winner(next_board) == player:
            tag = "immediate_win" if player == WHITE else "opponent_immediate_win"
            moves.append(CandidateMove(row=row, col=col, score=1_000_000, tags=[tag], reason=f"Creates five in a row for player {player}."))
    return sorted(moves, key=lambda move: (_distance_to_center(move.row, move.col), move.row, move.col))


def analyze_position(board: list[list[int]], ai_player: int = WHITE, limit: int = 32) -> StrategyReport:
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return StrategyReport([], [], [], "The board has no legal moves.")

    opponent = BLACK if ai_player == WHITE else WHITE
    immediate_wins = _find_immediate_wins(board, ai_player)
    opponent_wins = _find_immediate_wins(board, opponent)

    candidates_by_coord: dict[tuple[int, int], CandidateMove] = {}
    for row, col in _candidate_pool(board):
        attack_score, attack_tags = _score_for_player(board, row, col, ai_player, "create")
        defense_score, defense_tags = _score_for_player(board, row, col, opponent, "block")
        neighbor_score = _neighbor_count(board, row, col) * 85
        center_score = max(0, 14 - _distance_to_center(row, col)) * 22

        score = attack_score + int(defense_score * 0.92) + neighbor_score + center_score
        tags = list(dict.fromkeys(attack_tags + defense_tags))
        if neighbor_score:
            tags.append("near_existing_stones")
        if center_score >= 180:
            tags.append("center_control")

        reason_bits = []
        if tags:
            reason_bits.append(", ".join(tags[:4]))
        reason_bits.append(f"score {score}")
        candidates_by_coord[(row, col)] = CandidateMove(row=row, col=col, score=score, tags=tags, reason="; ".join(reason_bits))

    for move in immediate_wins:
        candidates_by_coord[(move.row, move.col)] = move
    for move in opponent_wins:
        existing = candidates_by_coord.get((move.row, move.col))
        if existing:
            existing.score = max(existing.score, 920_000)
            existing.tags = list(dict.fromkeys(["block_opponent_win"] + existing.tags))
            existing.reason = "Blocks an immediate opponent win."
        else:
            candidates_by_coord[(move.row, move.col)] = CandidateMove(
                row=move.row,
                col=move.col,
                score=920_000,
                tags=["block_opponent_win"],
                reason="Blocks an immediate opponent win.",
            )

    candidates = sorted(
        candidates_by_coord.values(),
        key=lambda move: (-move.score, _distance_to_center(move.row, move.col), move.row, move.col),
    )[:limit]

    brief_parts = [
        f"{len(legal_moves)} legal moves",
        f"{len(immediate_wins)} AI immediate wins",
        f"{len(opponent_wins)} opponent immediate threats",
        f"{len(candidates)} prioritized candidates",
    ]
    if candidates:
        top = candidates[0]
        brief_parts.append(f"top candidate row {top.row}, col {top.col}, score {top.score}")
    return StrategyReport(
        immediate_wins=immediate_wins,
        opponent_immediate_wins=opponent_wins,
        candidates=candidates,
        brief_analysis="; ".join(brief_parts) + ".",
    )


def choose_fallback_candidate(report: StrategyReport) -> CandidateMove:
    if report.immediate_wins:
        return report.immediate_wins[0]
    if report.opponent_immediate_wins:
        block = report.opponent_immediate_wins[0]
        block.tags = list(dict.fromkeys(["block_opponent_win"] + block.tags))
        block.score = max(block.score, 920_000)
        return block
    if report.candidates:
        return report.candidates[0]
    center = BOARD_SIZE // 2
    return CandidateMove(row=center, col=center, score=0, tags=["center_control"], reason="Default center move.")

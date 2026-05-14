from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .ai_client import AiClientError, AiTokenLimitError, parse_model_move, request_model_move
from .ai_prompt import build_ai_messages
from .ai_strategy import CandidateMove, analyze_position, choose_fallback_candidate
from .config import ALLOWED_ORIGINS, BLACK, WHITE
from .game_engine import GameRuleError, apply_move, get_status, validate_board
from .models import AiMoveRequest, AiMoveResponse, Diagnostics, ValidateMoveRequest, ValidateMoveResponse

app = FastAPI(title="Gomoku AI Arena", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/validate-move", response_model=ValidateMoveResponse)
async def validate_player_move(request: ValidateMoveRequest) -> ValidateMoveResponse:
    try:
        next_board = apply_move(request.board, request.row, request.col, request.player)
        status, winner = get_status(next_board)
    except GameRuleError as exc:
        return ValidateMoveResponse(valid=False, error=str(exc))
    return ValidateMoveResponse(valid=True, board=next_board, status=status, winner=winner)


def _response_from_candidate(
    board: list[list[int]],
    candidate: CandidateMove,
    source: str,
    model_called: bool,
    retry_count: int,
    candidate_count: int,
    brief_analysis: str,
    reason: Optional[str] = None,
) -> AiMoveResponse:
    next_board = apply_move(board, candidate.row, candidate.col, WHITE)
    status, winner = get_status(next_board)
    return AiMoveResponse(
        row=candidate.row,
        col=candidate.col,
        board=next_board,
        status=status,
        winner=winner,
        reason=reason or candidate.reason or "Selected by deterministic Gomoku analysis.",
        source=source,  # type: ignore[arg-type]
        diagnostics=Diagnostics(
            model_called=model_called,
            retry_count=retry_count,
            candidate_count=candidate_count,
            brief_analysis=brief_analysis,
            selected_score=candidate.score,
            selected_tags=candidate.tags,
        ),
    )


@app.post("/api/ai-move", response_model=AiMoveResponse)
async def ai_move(request: AiMoveRequest) -> AiMoveResponse:
    try:
        validate_board(request.board)
        status, _winner = get_status(request.board)
        if status != "ongoing":
            raise HTTPException(status_code=400, detail="The game is already finished.")

        report = analyze_position(request.board)
        if not report.candidates and not report.immediate_wins and not report.opponent_immediate_wins:
            raise HTTPException(status_code=400, detail="No legal moves are available.")

        if report.immediate_wins:
            candidate = report.immediate_wins[0]
            return _response_from_candidate(
                request.board,
                candidate,
                "heuristic_immediate_win",
                False,
                0,
                len(report.candidates),
                report.brief_analysis,
                "White has an immediate winning move.",
            )

        forced_block_only = bool(report.opponent_immediate_wins)
        last_error: Optional[str] = None
        attempts = 0

        for attempt in range(request.ai_settings.retry_count + 1):
            attempts = attempt
            try:
                constrained_report = report
                if forced_block_only:
                    block_coords = {(move.row, move.col) for move in report.opponent_immediate_wins}
                    constrained_report.candidates = [candidate for candidate in report.candidates if (candidate.row, candidate.col) in block_coords]
                messages = build_ai_messages(request.board, request.move_history, constrained_report, last_error)
                content = await request_model_move(request.config, request.ai_settings, messages)
                row, col, reason = parse_model_move(content, request.board)

                if forced_block_only and (row, col) not in {(move.row, move.col) for move in report.opponent_immediate_wins}:
                    raise AiClientError("Returned coordinate does not block Black's immediate win.")

                selected = next((candidate for candidate in report.candidates if candidate.row == row and candidate.col == col), None)
                if selected is None:
                    selected = CandidateMove(row=row, col=col, score=0, tags=["model_selected_legal_move"], reason=reason)
                return _response_from_candidate(
                    request.board,
                    selected,
                    "model",
                    True,
                    attempt,
                    len(report.candidates),
                    report.brief_analysis,
                    reason or selected.reason,
                )
            except AiClientError as exc:
                if isinstance(exc, AiTokenLimitError):
                    raise HTTPException(
                        status_code=400,
                        detail="对于思考模型，请适当增大max_tokens，防止下棋失败，本局游戏结束！",
                    ) from exc
                last_error = str(exc)

        fallback = choose_fallback_candidate(report)
        source = "heuristic_block" if forced_block_only else "fallback"
        fallback_reason = fallback.reason
        if last_error:
            fallback_reason = f"{fallback_reason} Model fallback used after: {last_error}"
        return _response_from_candidate(
            request.board,
            fallback,
            source,
            True,
            attempts,
            len(report.candidates),
            report.brief_analysis,
            fallback_reason,
        )
    except GameRuleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

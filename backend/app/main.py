from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .ai_client import AiClientError, parse_model_move, request_model_move
from .ai_prompt import build_ai_messages
from .config import ALLOWED_ORIGINS
from .game_engine import GameRuleError, apply_move, get_legal_moves, get_status, validate_board
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


def _response_from_model_move(
    board: list[list[int]],
    row: int,
    col: int,
    player: int,
    retry_count: int,
    legal_move_count: int,
) -> AiMoveResponse:
    next_board = apply_move(board, row, col, player)
    status, winner = get_status(next_board)
    return AiMoveResponse(
        row=row,
        col=col,
        board=next_board,
        status=status,
        winner=winner,
        source="model",
        diagnostics=Diagnostics(
            model_called=True,
            retry_count=retry_count,
            candidate_count=legal_move_count,
            brief_analysis="The move was selected by the model from the current board state and validated by the backend referee.",
        ),
    )


@app.post("/api/ai-move", response_model=AiMoveResponse)
async def ai_move(request: AiMoveRequest) -> AiMoveResponse:
    try:
        validate_board(request.board)
        status, _winner = get_status(request.board)
        if status != "ongoing":
            raise HTTPException(status_code=400, detail="The game is already finished.")

        legal_moves = get_legal_moves(request.board)
        if not legal_moves:
            raise HTTPException(status_code=400, detail="No legal moves are available.")

        last_error: Optional[str] = None
        total_attempts = request.ai_settings.retry_count + 1

        for retry_count in range(total_attempts):
            try:
                messages = build_ai_messages(request.board, request.move_history, request.player, last_error)
                content = await request_model_move(request.config, request.ai_settings, messages)
                row, col = parse_model_move(content, request.board, request.player)
                return _response_from_model_move(
                    request.board,
                    row,
                    col,
                    request.player,
                    retry_count,
                    len(legal_moves),
                )
            except AiClientError as exc:
                last_error = str(exc)

        raise HTTPException(
            status_code=502,
            detail=(
                f"Model move failed after {total_attempts} attempts. "
                f"The game has ended. Last error: {last_error or 'Unknown model error.'}"
            ),
        )
    except GameRuleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

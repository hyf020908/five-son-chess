from __future__ import annotations

from typing import Literal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .config import BOARD_SIZE, DEFAULT_MAX_TOKENS, DEFAULT_RETRY_COUNT, DEFAULT_TEMPERATURE

GameStatus = Literal["ongoing", "black_win", "white_win", "draw"]
MoveSource = Literal["model", "heuristic_immediate_win", "heuristic_block", "fallback"]


class Move(BaseModel):
    row: int = Field(ge=0, lt=BOARD_SIZE)
    col: int = Field(ge=0, lt=BOARD_SIZE)
    player: int = Field(ge=1, le=2)


class ModelConfig(BaseModel):
    base_url: str
    api_key: str
    model_name: str

    @field_validator("base_url", "api_key", "model_name")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("This field is required.")
        return stripped


class AiSettings(BaseModel):
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    max_tokens: int = Field(default=DEFAULT_MAX_TOKENS, ge=32, le=4096)
    retry_count: int = Field(default=DEFAULT_RETRY_COUNT, ge=0, le=4)
    reasoning_effort: Optional[str] = None


class ValidateMoveRequest(BaseModel):
    board: list[list[int]]
    move_history: list[Move] = Field(default_factory=list)
    row: int
    col: int
    player: int = Field(ge=1, le=2)


class ValidateMoveResponse(BaseModel):
    valid: bool
    board: Optional[list[list[int]]] = None
    status: Optional[GameStatus] = None
    winner: Optional[int] = None
    error: Optional[str] = None


class AiMoveRequest(BaseModel):
    board: list[list[int]]
    move_history: list[Move] = Field(default_factory=list)
    config: ModelConfig = Field(alias="model_config")
    ai_settings: AiSettings = Field(default_factory=AiSettings)


class Diagnostics(BaseModel):
    model_called: bool
    retry_count: int
    candidate_count: int
    brief_analysis: str
    selected_score: Optional[int] = None
    selected_tags: list[str] = Field(default_factory=list)


class AiMoveResponse(BaseModel):
    row: int
    col: int
    board: list[list[int]]
    status: GameStatus
    winner: Optional[int]
    reason: str
    source: MoveSource
    diagnostics: Diagnostics

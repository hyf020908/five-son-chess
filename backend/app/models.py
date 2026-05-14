from __future__ import annotations

from typing import Literal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .config import BOARD_SIZE, DEFAULT_RETRY_COUNT, DEFAULT_TEMPERATURE

GameStatus = Literal["ongoing", "black_win", "white_win", "draw"]
MoveSource = Literal["model"]


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
    retry_count: int = Field(default=DEFAULT_RETRY_COUNT, ge=0, le=3)


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
    player: int = Field(default=2, ge=1, le=2)
    config: ModelConfig = Field(alias="model_config")
    ai_settings: AiSettings = Field(default_factory=AiSettings)


class Diagnostics(BaseModel):
    model_called: bool
    retry_count: int
    candidate_count: int
    brief_analysis: str


class AiMoveResponse(BaseModel):
    row: int
    col: int
    board: list[list[int]]
    status: GameStatus
    winner: Optional[int]
    source: MoveSource
    diagnostics: Diagnostics

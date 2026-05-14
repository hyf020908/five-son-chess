from __future__ import annotations

from typing import Final

BOARD_SIZE: Final[int] = 15
EMPTY: Final[int] = 0
BLACK: Final[int] = 1
WHITE: Final[int] = 2
DEFAULT_TEMPERATURE: Final[float] = 0.25
DEFAULT_MAX_TOKENS: Final[int] = 220
DEFAULT_RETRY_COUNT: Final[int] = 2

ALLOWED_ORIGINS: Final[list[str]] = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
]

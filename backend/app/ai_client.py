from __future__ import annotations

import json
import re
from typing import Any

import httpx

from .game_engine import validate_move
from .models import AiSettings, ModelConfig


class AiClientError(RuntimeError):
    """Raised when a model service request or response cannot be used."""


class AiTokenLimitError(AiClientError):
    """Raised when the model response was truncated by max_tokens."""


def resolve_chat_completions_url(base_url: str) -> str:
    url = base_url.strip().rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    return f"{url}/chat/completions"


def extract_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise AiClientError("Model response is not valid JSON.") from None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise AiClientError("Model response contains malformed JSON.") from exc
    if not isinstance(parsed, dict):
        raise AiClientError("Model response JSON must be an object.")
    return parsed


def parse_model_move(content: str, board: list[list[int]], player: int = 2) -> tuple[int, int, str]:
    parsed = extract_json_object(content)
    row = parsed.get("row")
    col = parsed.get("col")
    reason = parsed.get("reason", "")
    if not isinstance(row, int) or not isinstance(col, int):
        raise AiClientError("Model JSON must include integer row and col.")
    validate_move(board, row, col, player)
    return row, col, str(reason)[:500]


async def request_model_move(
    model_config: ModelConfig,
    ai_settings: AiSettings,
    messages: list[dict[str, str]],
) -> str:
    payload: dict[str, Any] = {
        "model": model_config.model_name,
        "messages": messages,
        "temperature": ai_settings.temperature,
        "max_tokens": ai_settings.max_tokens,
    }
    if ai_settings.reasoning_effort:
        payload["reasoning_effort"] = ai_settings.reasoning_effort

    headers = {
        "Authorization": f"Bearer {model_config.api_key}",
        "Content-Type": "application/json",
    }
    url = resolve_chat_completions_url(model_config.base_url)

    timeout = httpx.Timeout(35.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = response.text[:300]
        raise AiClientError(f"Model service returned HTTP {response.status_code}: {detail}") from exc

    data = response.json()
    try:
        choice = data["choices"][0]
        finish_reason = choice.get("finish_reason")
        content = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AiClientError("Model response did not include choices[0].message.content.") from exc
    if finish_reason == "length":
        raise AiTokenLimitError("Model response was truncated because max_tokens was too small.")
    if not isinstance(content, str) or not content.strip():
        raise AiClientError("Model response content is empty.")
    return content

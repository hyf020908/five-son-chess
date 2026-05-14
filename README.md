# Gomoku AI Arena

Gomoku AI Arena is a full-stack web application for fair human vs AI Gomoku matches. The human player uses Black and moves first. The AI uses White and must play through a backend referee that validates the board, checks wins and draws, filters model output, and falls back to deterministic legal moves when needed.

## Features

- Vue 3, Vite, and TypeScript frontend with a polished board-focused interface.
- FastAPI backend with Pydantic models and deterministic Gomoku rules.
- OpenAI-compatible Chat Completions integration through `httpx`.
- Configurable `base_url`, `api_key`, `model_name`, `temperature`, and `max_tokens`.
- 15 x 15 board, zero-based row and column coordinates, last-move highlighting, star points, move history, and AI diagnostics.
- Strict backend validation for every move. A model can suggest a move, but it cannot force an illegal move.
- Threat-aware AI support with immediate win detection, forced blocking, candidate ranking, and fallback play.

## Project Structure

```text
backend/
  requirements.txt
  app/
    main.py
    models.py
    game_engine.py
    ai_client.py
    ai_prompt.py
    ai_strategy.py
    config.py
    rule_checks.py
frontend/
  package.json
  index.html
  vite.config.ts
  tsconfig.json
  src/
    App.vue
    main.ts
    api/client.ts
    components/
    styles/
    types/
README.md
.gitignore
```

## Requirements

- Python 3.10+
- Node.js 18+
- An OpenAI-compatible Chat Completions service

## Backend Setup

Run these commands from the project root:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r backend/requirements.txt
./.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Frontend Setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend uses `http://127.0.0.1:8000` as the default backend URL.

## Model Configuration

Fill in the setup panel before starting a match:

- `base_url`: The model service base URL. It may be a root URL, a `/v1` URL, or a full `/chat/completions` URL.
- `api_key`: Sent only with the AI move request. It is kept in page memory and is not stored in local storage.
- `model_name`: The model identifier used by the target service.
- `temperature`: Lower values usually make play more consistent.
- `max_tokens`: The maximum response length for the model move JSON.

The backend resolves the Chat Completions URL as follows:

- If `base_url` ends with `/chat/completions`, it is used directly.
- If `base_url` ends with `/v1`, `/chat/completions` is appended.
- Otherwise `/chat/completions` is appended.

## OpenAI-Compatible Services

Common local examples:

- vLLM: use the server's OpenAI-compatible `/v1` endpoint, for example `http://127.0.0.1:8000/v1`.
- LM Studio: use the local server `/v1` endpoint, commonly `http://127.0.0.1:1234/v1`.
- Ollama: use `http://127.0.0.1:11434/v1` when its OpenAI-compatible endpoint is enabled.

Use the model name exposed by the service. Some local services accept any non-empty API key placeholder, while hosted services usually require a real key.

## Game Rules

- The board is 15 x 15.
- Rows and columns are zero-based.
- Black is the human player and moves first.
- White is the AI player.
- Five or more consecutive stones horizontally, vertically, or diagonally wins.
- Occupied cells cannot be played.
- No moves are accepted after a win or draw.
- A full board with no winner is a draw.

## Fair Play Design

The backend is the referee. It validates the board, rejects illegal moves, applies moves, checks wins and draws, and validates all AI output. The model only receives public board state, recent move history, rules, candidate moves, and threat analysis. It never receives hidden information, and its move is accepted only if it is legal.

If the model returns malformed JSON, Markdown, an occupied coordinate, or an out-of-range coordinate, the backend retries with a clear correction message. If retries fail, the backend selects a legal fallback move from the ranked candidate set.

## AI Move Strategy

Before calling the model, the backend analyzes the position:

- Immediate White wins.
- Immediate Black wins that must be blocked.
- Open fours, closed fours, open threes, line extensions, center control, and nearby stones.
- A ranked candidate set near active stones, usually limited to a compact list for the prompt.

White's immediate winning move is played directly without model latency. If Black has an immediate win and White does not, the model is constrained to blocking candidates; fallback also blocks from legal moves.

## Backend API

### `GET /health`

Returns:

```json
{ "status": "ok" }
```

### `POST /api/validate-move`

Request:

```json
{
  "board": [[0]],
  "move_history": [],
  "row": 7,
  "col": 7,
  "player": 1
}
```

Response:

```json
{
  "valid": true,
  "board": [],
  "status": "ongoing",
  "winner": null,
  "error": null
}
```

### `POST /api/ai-move`

Request:

```json
{
  "board": [],
  "move_history": [],
  "model_config": {
    "base_url": "http://127.0.0.1:11434/v1",
    "api_key": "not-stored",
    "model_name": "local-model"
  },
  "ai_settings": {
    "temperature": 0.25,
    "max_tokens": 220,
    "retry_count": 2
  }
}
```

Response includes the selected move, updated board, game status, model or fallback source, reason, and diagnostics. Diagnostics never include the API key.

## FAQ

### How should `base_url` be filled in?

Use the OpenAI-compatible endpoint from your provider. A `/v1` endpoint is recommended when available.

### Why did the model return an illegal coordinate?

Language models can format or reason incorrectly. The backend treats model output as an untrusted suggestion and validates it before applying a move.

### Why does the AI sometimes play poorly?

The model quality, prompt following, temperature, and local service capability all affect play. Use a stronger model, lower temperature, and a service with reliable JSON responses for better results.

### How can AI strength be improved?

Use a stronger model, increase context quality, keep temperature low, and extend the deterministic strategy with deeper search or stronger pattern evaluation.

### Is the API key saved?

No. The frontend keeps it only in memory and sends it to the backend for each AI move request. It is not written to local storage or diagnostics.

### Why does the backend use `.venv`?

The virtual environment keeps Python dependencies inside the project and avoids changing system Python packages.

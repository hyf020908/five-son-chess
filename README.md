# Gomoku AI Arena

Gomoku AI Arena is a full-stack web application for fair Gomoku matches in two modes: Human vs AI and AI vs AI. In Human vs AI mode, the human player uses Black and moves first while the AI uses White. In AI vs AI mode, separate Black and White model configurations play automatically. Every AI move is selected by the configured model service, then validated by the backend referee before it is applied.

## Features

- Vue 3, Vite, and TypeScript frontend with a board-focused interface.
- FastAPI backend with Pydantic models and deterministic Gomoku rule validation.
- OpenAI-compatible Chat Completions integration through `httpx`.
- Configurable `base_url`, `api_key`, `model_name`, `temperature`, and `max_tokens`.
- Human vs AI and AI vs AI match modes, with separate model configuration for each AI side in AI vs AI mode.
- 15 x 15 board, zero-based row and column coordinates, last-move highlighting, star points, move history, and AI diagnostics.
- Strict backend validation for every move. A model can suggest a move, but it cannot force an illegal move.
- No heuristic AI moves, automatic wins, forced blocks, ranked candidate selection, or fallback play.
- Up to three retries for model move failures. If all attempts fail, the current game ends and the UI shows the error.

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

- Mode:
  - Human vs AI uses one AI model. The human plays Black and the AI plays White.
  - AI vs AI uses two AI model configurations, one for Black and one for White. The match runs automatically after start.
- `base_url`: The model service base URL. It may be a root URL, a `/v1` URL, or a full `/chat/completions` URL.
- `api_key`: Sent only with the AI move request. It is kept in page memory and is not stored in local storage.
- `model_name`: The model identifier used by the target service.
- `temperature`: Lower values usually make play more consistent.
- `max_tokens`: The maximum response length for the model move JSON. The default is 256 and the minimum is 128.
- `retry_count`: The number of retries after an initial failed model call. The default is 3 and the maximum is 3.

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
- Black always moves first.
- In Human vs AI mode, Black is the human player and White is the AI player.
- In AI vs AI mode, Black AI and White AI play automatically.
- Five or more consecutive stones horizontally, vertically, or diagonally wins.
- Occupied cells cannot be played.
- No moves are accepted after a win or draw.
- A full board with no winner is a draw.

## Fair Play Design

The backend is the referee. It validates the board, rejects illegal moves, applies moves, checks wins and draws, and validates all AI output. Models receive only public board state, recent move history, the rules, and the legal empty coordinates. They never receive hidden information or backend-ranked move suggestions.

If the model returns malformed JSON, Markdown, an occupied coordinate, or an out-of-range coordinate, the backend retries with a clear correction message. The backend does not choose a substitute move. If all retries fail, the backend returns an error and the frontend ends the current game in both Human vs AI and AI vs AI modes.

If an OpenAI-compatible service reports that the response was cut off because `max_tokens` was too small, the frontend ends the current game and shows a non-modal status message asking the user to increase `max_tokens` for reasoning models.

## AI Move Policy

The application is model-only for AI decisions:

- No deterministic immediate-win move is played before calling the model.
- No deterministic forced block is played before calling the model.
- No ranked candidate list is supplied to the model.
- No fallback move is selected after model failure.
- The backend only validates legality and game rules after the model returns a coordinate.

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
  "player": 2,
  "model_config": {
    "base_url": "http://127.0.0.1:11434/v1",
    "api_key": "not-stored",
    "model_name": "local-model"
  },
  "ai_settings": {
    "temperature": 0.25,
    "max_tokens": 256,
    "retry_count": 3
  }
}
```

`player` is `1` for Black AI and `2` for White AI. If omitted, it defaults to `2` for backwards compatibility. A successful response always contains a model-selected move, updated board, game status, reason, and diagnostics. Diagnostics never include the API key.

If the model call fails after all attempts, the endpoint returns an error instead of a move. The frontend treats this as a terminal game failure and disables further play until the match is restarted.

## FAQ

### How should `base_url` be filled in?

Use the OpenAI-compatible endpoint from your provider. A `/v1` endpoint is recommended when available.

### Why did the model return an illegal coordinate?

Language models can format or reason incorrectly. The backend treats model output as an untrusted suggestion, validates it, and retries if the move is invalid.

### Why does the game end after model errors?

The application is intentionally model-only. It does not hide model failures behind deterministic fallback moves. After the retry budget is exhausted, the match ends and the UI shows the error.

### Why does the AI sometimes play poorly?

The model quality, prompt following, temperature, and local service capability all affect play. Use a stronger model, lower temperature, and a service with reliable JSON responses for better results.

### How can AI strength be improved?

Use a stronger model, keep temperature low, increase context quality in the prompt, or connect a model with better board-game reasoning.

### Is the API key saved?

No. The frontend keeps it only in memory and sends it to the backend for each AI move request. It is not written to local storage or diagnostics.

### Why does the backend use `.venv`?

The virtual environment keeps Python dependencies inside the project and avoids changing system Python packages.

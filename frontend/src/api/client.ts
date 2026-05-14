import type { AiMoveResponse, AiSettings, Cell, ModelConfig, Move, ValidateMoveResponse } from '../types/game';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function readJson<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = payload?.detail ?? payload?.error ?? `Request failed with HTTP ${response.status}`;
    throw new Error(String(detail));
  }
  return payload as T;
}

export async function validateMove(board: Cell[][], moveHistory: Move[], row: number, col: number, player: 1 | 2) {
  const response = await fetch(`${API_BASE_URL}/api/validate-move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ board, move_history: moveHistory, row, col, player }),
  });
  return readJson<ValidateMoveResponse>(response);
}

export async function requestAiMove(
  board: Cell[][],
  moveHistory: Move[],
  modelConfig: ModelConfig,
  aiSettings: AiSettings,
  player: 1 | 2 = 2,
) {
  const response = await fetch(`${API_BASE_URL}/api/ai-move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ board, move_history: moveHistory, player, model_config: modelConfig, ai_settings: aiSettings }),
  });
  return readJson<AiMoveResponse>(response);
}

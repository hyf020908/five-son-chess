export type Cell = 0 | 1 | 2;
export type GameStatus = 'waiting' | 'ongoing' | 'black_win' | 'white_win' | 'draw';

export interface Move {
  row: number;
  col: number;
  player: 1 | 2;
}

export interface ModelConfig {
  base_url: string;
  api_key: string;
  model_name: string;
}

export interface AiSettings {
  temperature: number;
  max_tokens: number;
  retry_count: number;
}

export interface Diagnostics {
  model_called: boolean;
  retry_count: number;
  candidate_count: number;
  brief_analysis: string;
  selected_score: number | null;
  selected_tags: string[];
}

export interface AiMoveResponse {
  row: number;
  col: number;
  board: Cell[][];
  status: Exclude<GameStatus, 'waiting'>;
  winner: 1 | 2 | null;
  reason: string;
  source: 'model' | 'heuristic_immediate_win' | 'heuristic_block' | 'fallback';
  diagnostics: Diagnostics;
}

export interface ValidateMoveResponse {
  valid: boolean;
  board: Cell[][] | null;
  status: Exclude<GameStatus, 'waiting'> | null;
  winner: 1 | 2 | null;
  error: string | null;
}

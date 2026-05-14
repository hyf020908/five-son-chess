export type Cell = 0 | 1 | 2;
export type GameStatus = 'waiting' | 'ongoing' | 'black_win' | 'white_win' | 'draw';
export type GameMode = 'human_ai' | 'ai_ai';

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
  retry_count: number;
}

export interface Diagnostics {
  model_called: boolean;
  retry_count: number;
  candidate_count: number;
  brief_analysis: string;
}

export interface AiMoveResponse {
  row: number;
  col: number;
  board: Cell[][];
  status: Exclude<GameStatus, 'waiting'>;
  winner: 1 | 2 | null;
  source: 'model';
  diagnostics: Diagnostics;
}

export interface ValidateMoveResponse {
  valid: boolean;
  board: Cell[][] | null;
  status: Exclude<GameStatus, 'waiting'> | null;
  winner: 1 | 2 | null;
  error: string | null;
}

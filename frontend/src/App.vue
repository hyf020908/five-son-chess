<script setup lang="ts">
import { reactive, ref } from 'vue';
import { requestAiMove, validateMove } from './api/client';
import AiDiagnosticsPanel from './components/AiDiagnosticsPanel.vue';
import GameStatusPanel from './components/GameStatusPanel.vue';
import GomokuBoard from './components/GomokuBoard.vue';
import ModelConfigPanel from './components/ModelConfigPanel.vue';
import MoveHistory from './components/MoveHistory.vue';
import type { AiSettings, Cell, Diagnostics, GameStatus, ModelConfig, Move } from './types/game';

const BOARD_SIZE = 15;

function createBoard(): Cell[][] {
  return Array.from({ length: BOARD_SIZE }, () => Array.from({ length: BOARD_SIZE }, () => 0 as Cell));
}

const board = ref<Cell[][]>(createBoard());
const moveHistory = ref<Move[]>([]);
const gameStatus = ref<GameStatus>('waiting');
const aiThinking = ref(false);
const lastMove = ref<Move | null>(null);
const aiReason = ref('');
const aiSource = ref('');
const diagnostics = ref<Diagnostics | null>(null);
const errorMessage = ref('');
const gameStarted = ref(false);

const modelConfig = reactive<ModelConfig>({
  base_url: 'http://127.0.0.1:11434/v1',
  api_key: '',
  model_name: '',
});

const aiSettings = reactive<AiSettings>({
  temperature: 0.25,
  max_tokens: 220,
  retry_count: 2,
});

function resetGame() {
  board.value = createBoard();
  moveHistory.value = [];
  gameStatus.value = gameStarted.value ? 'ongoing' : 'waiting';
  aiThinking.value = false;
  lastMove.value = null;
  aiReason.value = '';
  aiSource.value = '';
  diagnostics.value = null;
  errorMessage.value = '';
}

function validateConfig(): boolean {
  if (!modelConfig.base_url.trim()) {
    errorMessage.value = 'Base URL is required.';
    return false;
  }
  if (!modelConfig.api_key.trim()) {
    errorMessage.value = 'API key is required for the model service.';
    return false;
  }
  if (!modelConfig.model_name.trim()) {
    errorMessage.value = 'Model name is required.';
    return false;
  }
  return true;
}

function startGame() {
  errorMessage.value = '';
  if (!validateConfig()) return;
  gameStarted.value = true;
  resetGame();
  gameStatus.value = 'ongoing';
}

async function onPlace(row: number, col: number) {
  if (!gameStarted.value || aiThinking.value || gameStatus.value !== 'ongoing') return;
  if (board.value[row][col] !== 0) return;

  errorMessage.value = '';
  if (!validateConfig()) return;

  try {
    const playerMove: Move = { row, col, player: 1 };
    const validation = await validateMove(board.value, moveHistory.value, row, col, 1);
    if (!validation.valid || !validation.board || !validation.status) {
      errorMessage.value = validation.error || 'Move was rejected by the backend.';
      return;
    }

    board.value = validation.board;
    moveHistory.value = [...moveHistory.value, playerMove];
    lastMove.value = playerMove;
    gameStatus.value = validation.status;

    if (validation.status !== 'ongoing') return;

    aiThinking.value = true;
    const aiResponse = await requestAiMove(board.value, moveHistory.value, modelConfig, aiSettings);
    const aiMove: Move = { row: aiResponse.row, col: aiResponse.col, player: 2 };
    board.value = aiResponse.board;
    moveHistory.value = [...moveHistory.value, aiMove];
    lastMove.value = aiMove;
    gameStatus.value = aiResponse.status;
    aiReason.value = aiResponse.reason;
    aiSource.value = aiResponse.source;
    diagnostics.value = aiResponse.diagnostics;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Unexpected request failure.';
  } finally {
    aiThinking.value = false;
  }
}
</script>

<template>
  <main class="app-shell">
    <header class="hero">
      <div>
        <p class="eyebrow">Fair human vs AI gomoku match</p>
        <h1>Gomoku AI Arena</h1>
      </div>
      <div class="hero-badge">
        <span>15 x 15</span>
        <strong>Black first</strong>
      </div>
    </header>

    <div class="layout-grid">
      <aside class="left-column">
        <ModelConfigPanel
          :model-config="modelConfig"
          :ai-settings="aiSettings"
          :game-started="gameStarted"
          :ai-thinking="aiThinking"
          @start="startGame"
          @reset="resetGame"
        />
        <GameStatusPanel
          :status="gameStatus"
          :ai-thinking="aiThinking"
          :error-message="errorMessage"
          :move-count="moveHistory.length"
        />
      </aside>

      <GomokuBoard :board="board" :disabled="!gameStarted || aiThinking || gameStatus !== 'ongoing'" :last-move="lastMove" @place="onPlace" />

      <aside class="right-column">
        <AiDiagnosticsPanel :reason="aiReason" :source="aiSource" :diagnostics="diagnostics" />
        <MoveHistory :moves="moveHistory" />
      </aside>
    </div>
  </main>
</template>

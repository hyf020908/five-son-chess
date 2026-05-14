<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { requestAiMove, validateMove } from './api/client';
import AiDiagnosticsPanel from './components/AiDiagnosticsPanel.vue';
import GameStatusPanel from './components/GameStatusPanel.vue';
import GomokuBoard from './components/GomokuBoard.vue';
import ModelConfigPanel from './components/ModelConfigPanel.vue';
import MoveHistory from './components/MoveHistory.vue';
import type { AiSettings, Cell, Diagnostics, GameMode, GameStatus, ModelConfig, Move } from './types/game';

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
const gameResultDialogVisible = ref(false);
const tokenLimitGameOverMessage = 'For reasoning models, increase max_tokens to prevent move failures. This game is over!';
const gameMode = ref<GameMode>('human_ai');
let aiVsAiRunId = 0;

const modelConfig = reactive<ModelConfig>({
  base_url: 'http://127.0.0.1:11434/v1',
  api_key: '',
  model_name: '',
});

const blackModelConfig = reactive<ModelConfig>({
  base_url: 'http://127.0.0.1:11434/v1',
  api_key: '',
  model_name: '',
});

const aiSettings = reactive<AiSettings>({
  temperature: 0.25,
  max_tokens: 256,
  retry_count: 2,
});

const gameResultMessage = computed(() => {
  if (gameMode.value === 'ai_ai') {
    if (gameStatus.value === 'black_win') return `${blackModelConfig.model_name.trim() || 'Black'} model wins`;
    if (gameStatus.value === 'white_win') return `${modelConfig.model_name.trim() || 'White'} model wins`;
    if (gameStatus.value === 'draw') return 'Draw';
    return '';
  }
  if (gameStatus.value === 'black_win') return '✅ Congratulations, you won the match!';
  if (gameStatus.value === 'white_win') return '😧 Keep trying! Better luck next time!';
  if (gameStatus.value === 'draw') return '♟️ Draw';
  return '';
});

watch(gameStatus, (status) => {
  gameResultDialogVisible.value = ['black_win', 'white_win', 'draw'].includes(status);
});

function resetGame() {
  aiVsAiRunId += 1;
  board.value = createBoard();
  moveHistory.value = [];
  gameStatus.value = gameStarted.value ? 'ongoing' : 'waiting';
  aiThinking.value = false;
  lastMove.value = null;
  aiReason.value = '';
  aiSource.value = '';
  diagnostics.value = null;
  errorMessage.value = '';
  gameResultDialogVisible.value = false;
}

function validateModelConfig(config: ModelConfig, label: string): boolean {
  if (!config.base_url.trim()) {
    errorMessage.value = `${label} Base URL is required.`;
    return false;
  }
  if (!config.api_key.trim()) {
    errorMessage.value = `${label} API key is required.`;
    return false;
  }
  if (!config.model_name.trim()) {
    errorMessage.value = `${label} Model name is required.`;
    return false;
  }
  return true;
}

function validateConfig(): boolean {
  if (gameMode.value === 'ai_ai' && !validateModelConfig(blackModelConfig, 'Black model')) return false;
  if (!validateModelConfig(modelConfig, gameMode.value === 'ai_ai' ? 'White model' : 'AI model')) return false;
  if (!Number.isFinite(aiSettings.max_tokens) || aiSettings.max_tokens < 128) {
    errorMessage.value = 'Max tokens must be at least 128.';
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
  if (gameMode.value === 'ai_ai') {
    void runAiVsAiGame(aiVsAiRunId);
  }
}

function onModeChange(mode: GameMode) {
  if (aiThinking.value) return;
  gameMode.value = mode;
  gameStarted.value = false;
  resetGame();
}

async function applyAiMove(player: 1 | 2, config: ModelConfig) {
  const aiResponse = await requestAiMove(board.value, moveHistory.value, config, aiSettings, player);
  const aiMove: Move = { row: aiResponse.row, col: aiResponse.col, player };
  board.value = aiResponse.board;
  moveHistory.value = [...moveHistory.value, aiMove];
  lastMove.value = aiMove;
  gameStatus.value = aiResponse.status;
  aiReason.value = aiResponse.reason;
  aiSource.value = aiResponse.source;
  diagnostics.value = aiResponse.diagnostics;
}

function endGameForTokenLimit(message: string) {
  errorMessage.value = message;
  gameStarted.value = false;
  gameStatus.value = 'waiting';
  gameResultDialogVisible.value = false;
  aiVsAiRunId += 1;
}

async function runAiVsAiGame(runId: number) {
  while (runId === aiVsAiRunId && gameStarted.value && gameStatus.value === 'ongoing') {
    const player = (moveHistory.value.length % 2 === 0 ? 1 : 2) as 1 | 2;
    const config = player === 1 ? blackModelConfig : modelConfig;
    aiThinking.value = true;
    try {
      await applyAiMove(player, config);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unexpected request failure.';
      if (message === tokenLimitGameOverMessage) {
        endGameForTokenLimit(message);
      } else {
        errorMessage.value = message;
        gameStarted.value = false;
        gameStatus.value = 'waiting';
        aiVsAiRunId += 1;
      }
      return;
    } finally {
      aiThinking.value = false;
    }

    if (gameStatus.value !== 'ongoing') return;
    await new Promise((resolve) => window.setTimeout(resolve, 300));
  }
}

async function onPlace(row: number, col: number) {
  if (gameMode.value !== 'human_ai' || !gameStarted.value || aiThinking.value || gameStatus.value !== 'ongoing') return;
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
    await applyAiMove(2, modelConfig);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unexpected request failure.';
    errorMessage.value = message;
    if (message === tokenLimitGameOverMessage) {
      endGameForTokenLimit(message);
    }
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
          :game-mode="gameMode"
          :model-config="modelConfig"
          :black-model-config="blackModelConfig"
          :ai-settings="aiSettings"
          :game-started="gameStarted"
          :ai-thinking="aiThinking"
          @mode-change="onModeChange"
          @start="startGame"
          @reset="resetGame"
        />
        <GameStatusPanel
          :status="gameStatus"
          :ai-thinking="aiThinking"
          :error-message="errorMessage"
          :move-count="moveHistory.length"
          :game-mode="gameMode"
        />
      </aside>

      <GomokuBoard
        :board="board"
        :disabled="gameMode === 'ai_ai' || !gameStarted || aiThinking || gameStatus !== 'ongoing'"
        :last-move="lastMove"
        @place="onPlace"
      />

      <aside class="right-column">
        <AiDiagnosticsPanel :reason="aiReason" :source="aiSource" :diagnostics="diagnostics" />
        <MoveHistory :moves="moveHistory" />
      </aside>
    </div>

    <div v-if="gameResultDialogVisible" class="result-dialog-backdrop" role="presentation">
      <section class="result-dialog" role="dialog" aria-modal="true" aria-labelledby="result-dialog-title">
        <h2 id="result-dialog-title">{{ gameResultMessage }}</h2>
        <button class="primary-button result-dialog-button" type="button" @click="gameResultDialogVisible = false">Confirm</button>
      </section>
    </div>
  </main>
</template>

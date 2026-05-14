<script setup lang="ts">
import type { GameStatus } from '../types/game';

const props = defineProps<{
  status: GameStatus;
  aiThinking: boolean;
  errorMessage: string;
  moveCount: number;
}>();

function statusText() {
  if (props.errorMessage) return 'Action required';
  if (props.aiThinking) return 'AI is thinking';
  if (props.status === 'waiting') return 'Waiting for setup';
  if (props.status === 'ongoing') return 'Black to move';
  if (props.status === 'black_win') return 'Black wins';
  if (props.status === 'white_win') return 'White wins';
  return 'Draw';
}
</script>

<template>
  <section class="panel status-panel">
    <p class="eyebrow">Game status</p>
    <h2>{{ statusText() }}</h2>
    <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
    <p v-else class="muted">{{ moveCount }} moves played. Black is human, White is AI.</p>
  </section>
</template>

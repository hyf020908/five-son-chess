<script setup lang="ts">
import type { Move } from '../types/game';

defineProps<{
  moves: Move[];
}>();
</script>

<template>
  <section class="panel history-panel">
    <div class="panel-heading">
      <p class="eyebrow">Record</p>
      <h2>Move history</h2>
    </div>
    <ol class="move-list">
      <li v-for="(move, index) in moves" :key="`${index}-${move.row}-${move.col}`" :class="{ active: index === moves.length - 1 }">
        <span class="move-number">{{ index + 1 }}</span>
        <span class="player-pill" :class="move.player === 1 ? 'black-pill' : 'white-pill'">{{ move.player === 1 ? 'Black' : 'White' }}</span>
        <span>row {{ move.row }}, col {{ move.col }}</span>
      </li>
    </ol>
    <p v-if="moves.length === 0" class="empty-state">No moves yet.</p>
  </section>
</template>

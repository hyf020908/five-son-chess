<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Cell, Move } from '../types/game';

const props = defineProps<{
  board: Cell[][];
  disabled: boolean;
  lastMove: Move | null;
}>();

const emit = defineEmits<{
  place: [row: number, col: number];
}>();

const hover = ref<{ row: number; col: number } | null>(null);
const starPoints = new Set(['3-3', '3-7', '3-11', '7-3', '7-7', '7-11', '11-3', '11-7', '11-11']);

const canPreview = computed(() => {
  if (!hover.value || props.disabled) return false;
  return props.board[hover.value.row]?.[hover.value.col] === 0;
});

function place(row: number, col: number) {
  if (props.disabled || props.board[row][col] !== 0) return;
  emit('place', row, col);
}
</script>

<template>
  <section class="board-shell">
    <div class="board" role="grid" aria-label="Gomoku board">
      <button
        v-for="(_, index) in 225"
        :key="index"
        class="intersection"
        :class="{
          occupied: board[Math.floor((index - 1 + 1) / 15)][index % 15] !== 0,
          disabled,
          last: lastMove?.row === Math.floor(index / 15) && lastMove?.col === index % 15,
        }"
        type="button"
        :aria-label="`row ${Math.floor(index / 15)}, col ${index % 15}`"
        :disabled="disabled || board[Math.floor(index / 15)][index % 15] !== 0"
        @mouseenter="hover = { row: Math.floor(index / 15), col: index % 15 }"
        @mouseleave="hover = null"
        @click="place(Math.floor(index / 15), index % 15)"
      >
        <span v-if="starPoints.has(`${Math.floor(index / 15)}-${index % 15}`)" class="star"></span>
        <span
          v-if="board[Math.floor(index / 15)][index % 15] !== 0"
          class="stone"
          :class="board[Math.floor(index / 15)][index % 15] === 1 ? 'black' : 'white'"
        ></span>
        <span
          v-else-if="canPreview && hover?.row === Math.floor(index / 15) && hover?.col === index % 15"
          class="preview-stone"
        ></span>
      </button>
    </div>
  </section>
</template>

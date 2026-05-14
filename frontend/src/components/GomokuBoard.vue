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

const boardSize = computed(() => props.board.length);
const svgExtent = computed(() => Math.max(boardSize.value - 1, 0));
const points = computed(() =>
  Array.from({ length: boardSize.value * boardSize.value }, (_, index) => ({
    index,
    row: Math.floor(index / boardSize.value),
    col: index % boardSize.value,
  })),
);
const lines = computed(() => Array.from({ length: boardSize.value }, (_, index) => index));

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
    <div class="board" role="grid" aria-label="Gomoku board" :style="{ '--board-size': boardSize }">
      <svg class="board-lines" :viewBox="`0 0 ${svgExtent} ${svgExtent}`" preserveAspectRatio="none" aria-hidden="true">
        <line v-for="line in lines" :key="`v-${line}`" :x1="line" y1="0" :x2="line" :y2="svgExtent" />
        <line v-for="line in lines" :key="`h-${line}`" x1="0" :y1="line" :x2="svgExtent" :y2="line" />
      </svg>
      <button
        v-for="point in points"
        :key="point.index"
        class="intersection"
        :class="{
          occupied: board[point.row][point.col] !== 0,
          disabled,
          last: lastMove?.row === point.row && lastMove?.col === point.col,
        }"
        type="button"
        :aria-label="`row ${point.row}, col ${point.col}`"
        :disabled="disabled || board[point.row][point.col] !== 0"
        @mouseenter="hover = { row: point.row, col: point.col }"
        @mouseleave="hover = null"
        @click="place(point.row, point.col)"
      >
        <span v-if="starPoints.has(`${point.row}-${point.col}`)" class="star"></span>
        <span
          v-if="board[point.row][point.col] !== 0"
          class="stone"
          :class="board[point.row][point.col] === 1 ? 'black' : 'white'"
        ></span>
        <span v-else-if="canPreview && hover?.row === point.row && hover?.col === point.col" class="preview-stone"></span>
      </button>
    </div>
  </section>
</template>

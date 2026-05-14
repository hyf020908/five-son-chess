<script setup lang="ts">
import type { Diagnostics } from '../types/game';

defineProps<{
  source: string;
  diagnostics: Diagnostics | null;
}>();
</script>

<template>
  <section class="panel diagnostics-panel">
    <div class="panel-heading">
      <p class="eyebrow">AI analysis</p>
      <h2>Decision details</h2>
    </div>
    <dl class="metrics">
      <div>
        <dt>Source</dt>
        <dd>{{ source || 'none' }}</dd>
      </div>
      <div>
        <dt>Retries used</dt>
        <dd>{{ diagnostics?.retry_count ?? 0 }}</dd>
      </div>
      <div>
        <dt>Legal moves</dt>
        <dd>{{ diagnostics?.candidate_count ?? 0 }}</dd>
      </div>
    </dl>
    <p class="muted">{{ diagnostics?.brief_analysis || 'The backend will report model-move validation details after an AI move.' }}</p>
  </section>
</template>

<script setup lang="ts">
import type { Diagnostics } from '../types/game';

defineProps<{
  reason: string;
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
    <p class="reason">{{ reason || 'No AI move has been requested yet.' }}</p>
    <dl class="metrics">
      <div>
        <dt>Source</dt>
        <dd>{{ source || 'none' }}</dd>
      </div>
      <div>
        <dt>Retries</dt>
        <dd>{{ diagnostics?.retry_count ?? 0 }}</dd>
      </div>
      <div>
        <dt>Candidates</dt>
        <dd>{{ diagnostics?.candidate_count ?? 0 }}</dd>
      </div>
      <div>
        <dt>Score</dt>
        <dd>{{ diagnostics?.selected_score ?? 'n/a' }}</dd>
      </div>
    </dl>
    <p class="muted">{{ diagnostics?.brief_analysis || 'The backend will summarize threats and candidates after White moves.' }}</p>
    <div v-if="diagnostics?.selected_tags.length" class="tag-row">
      <span v-for="tag in diagnostics.selected_tags" :key="tag">{{ tag }}</span>
    </div>
  </section>
</template>

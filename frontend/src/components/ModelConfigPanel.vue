<script setup lang="ts">
import type { AiSettings, ModelConfig } from '../types/game';

defineProps<{
  modelConfig: ModelConfig;
  aiSettings: AiSettings;
  gameStarted: boolean;
  aiThinking: boolean;
}>();

const emit = defineEmits<{
  start: [];
  reset: [];
}>();
</script>

<template>
  <section class="panel config-panel">
    <div class="panel-heading">
      <p class="eyebrow">Model service</p>
      <h2>Match setup</h2>
    </div>

    <label>
      <span>Base URL</span>
      <input v-model="modelConfig.base_url" placeholder="http://127.0.0.1:8000/v1" autocomplete="off" />
    </label>

    <label>
      <span>API key</span>
      <input v-model="modelConfig.api_key" type="password" placeholder="sk-..." autocomplete="off" />
    </label>

    <label>
      <span>Model name</span>
      <input v-model="modelConfig.model_name" placeholder="gpt-4.1-mini or local-model" autocomplete="off" />
    </label>

    <div class="form-grid">
      <label>
        <span>Temperature</span>
        <input v-model.number="aiSettings.temperature" type="number" min="0" max="2" step="0.05" />
      </label>
      <label>
        <span>Max tokens</span>
        <input v-model.number="aiSettings.max_tokens" type="number" min="128" max="4096" step="16" />
      </label>
    </div>

    <div class="button-row">
      <button class="primary-button" type="button" :disabled="aiThinking" @click="emit('start')">
        {{ gameStarted ? 'Apply setup' : 'Start game' }}
      </button>
      <button class="secondary-button" type="button" :disabled="aiThinking" @click="emit('reset')">Restart</button>
    </div>
  </section>
</template>

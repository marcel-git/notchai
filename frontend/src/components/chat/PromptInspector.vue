<template>
  <div v-if="open" class="overlay" @click.self="close">
    <section class="dialog" role="dialog" aria-modal="true" aria-labelledby="prompt-title">
      <header class="dialog-header">
        <div>
          <h2 id="prompt-title">{{ editable ? 'Customize system prompt' : 'System prompt' }}</h2>
          <p v-if="inspection" class="settings-line">
            {{ inspection.model_name }} · {{ inspection.num_predict }} tokens ·
            temperature {{ inspection.temperature }} · top-p {{ inspection.top_p }}
          </p>
        </div>
        <button class="close-button" type="button" aria-label="Close prompt inspection" :disabled="saving" @click="close">
          ×
        </button>
      </header>

      <p v-if="loading" class="status" role="status">Building prompt preview...</p>
      <article v-else-if="inspection" class="system-prompt">
        <h3>Instructions sent to the model</h3>
        <p v-if="editable" class="edit-help">
          Customize the instructions for this conversation. Your changes are saved only to this conversation.
        </p>
        <textarea
          v-if="editable"
          v-model="systemPromptDraft"
          aria-label="System prompt"
          spellcheck="false"
        ></textarea>
        <pre v-else-if="inspection.system_prompt">{{ inspection.system_prompt }}</pre>
        <p v-else class="empty-prompt">No system prompt is configured for this conversation.</p>
      </article>
      <p v-if="error" class="status error" role="alert">{{ error }}</p>

      <footer v-if="editable" class="dialog-actions">
        <button type="button" class="cancel-button" :disabled="saving" @click="close">
          Cancel
        </button>
        <button
          type="button"
          class="confirm-button"
          :disabled="loading || saving || !inspection"
          @click="emit('confirm', systemPromptDraft)"
        >
          {{ saving ? 'Starting...' : 'Use prompt and start' }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
  import { ref, watch } from 'vue'
  import type { PromptInspection as PromptInspectionData } from '../../types/roleplay'

  const props = withDefaults(defineProps<{
    open: boolean
    loading: boolean
    error: string
    inspection: PromptInspectionData | null
    editable?: boolean
    saving?: boolean
  }>(), {
    editable: false,
    saving: false,
  })

  const emit = defineEmits<{
    close: []
    confirm: [systemPrompt: string]
  }>()

  const systemPromptDraft = ref('')

  watch(
    () => props.inspection?.system_prompt,
    (systemPrompt) => {
      systemPromptDraft.value = systemPrompt ?? ''
    },
    { immediate: true },
  )

  function close() {
    if (!props.saving) emit('close')
  }
</script>

<style scoped>
  .overlay {
    position: fixed;
    z-index: 10;
    inset: 0;
    display: grid;
    place-items: center;
    padding: 20px;
    background: rgba(4, 8, 5, 0.78);
    backdrop-filter: blur(4px);
  }

  .dialog {
    display: flex;
    width: min(820px, 100%);
    max-height: min(85vh, 900px);
    flex-direction: column;
    overflow: hidden;
    border: 1px solid rgba(211, 218, 201, 0.15);
    border-radius: 12px;
    background: #17211b;
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.42);
  }

  .dialog-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    padding: 20px 22px;
    border-bottom: 1px solid var(--color-line);
  }

  h2 {
    margin: 0;
    color: #e5e5d9;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 22px;
    font-weight: 500;
  }

  .settings-line,
  .status {
    margin: 8px 0 0;
    color: var(--color-muted);
    font-size: 11px;
    line-height: 1.6;
  }

  .close-button {
    width: 30px;
    height: 30px;
    border-radius: 6px;
    background: transparent;
    color: var(--color-muted);
    font-size: 23px;
  }

  .close-button:hover {
    background: rgba(255, 255, 255, 0.06);
    color: var(--color-text);
  }

  .close-button:disabled,
  .dialog-actions button:disabled {
    cursor: wait;
    opacity: 0.55;
  }

  .system-prompt {
    display: flex;
    margin: 18px 22px 22px;
    min-height: 0;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid var(--color-line);
    border-radius: 8px;
    background: #111813;
  }

  .system-prompt h3 {
    margin: 0;
    padding: 9px 12px;
    border-bottom: 1px solid var(--color-line);
    color: var(--color-gold);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
  }

  .system-prompt pre {
    margin: 0;
    padding: 14px;
    overflow: auto;
    max-height: 60vh;
    color: #c3c9c0;
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
    font-size: 11px;
    line-height: 1.65;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }

  .edit-help {
    margin: 0;
    padding: 11px 14px 0;
    color: var(--color-muted);
    font-size: 11px;
    line-height: 1.5;
  }

  .system-prompt textarea {
    box-sizing: border-box;
    width: 100%;
    min-height: min(52vh, 460px);
    padding: 14px;
    border: 0;
    background: transparent;
    color: #d4dacf;
    font: 12px/1.7 'DM Sans', 'Segoe UI', sans-serif;
    resize: vertical;
  }

  .system-prompt textarea:focus {
    outline: 2px solid rgba(191, 166, 105, 0.45);
    outline-offset: -2px;
  }

  .empty-prompt {
    margin: 0;
    padding: 18px 22px 22px;
    color: var(--color-muted);
    font-size: 11px;
  }

  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 9px;
    padding: 14px 22px 18px;
    border-top: 1px solid var(--color-line);
  }

  .dialog-actions button {
    min-height: 34px;
    padding: 0 13px;
    border: 1px solid rgba(211, 218, 201, 0.16);
    border-radius: 6px;
    background: transparent;
    color: #aeb6aa;
    font-size: 11px;
  }

  .dialog-actions .confirm-button {
    border-color: rgba(196, 169, 110, 0.45);
    background: rgba(60, 91, 65, 0.5);
    color: #e8e5d7;
    font-weight: 600;
  }

  .dialog-actions button:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.08);
    color: var(--color-text);
  }

  .dialog-actions .confirm-button:hover:not(:disabled) {
    background: rgba(66, 101, 71, 0.72);
  }

  .status {
    padding: 0 22px 22px;
  }

  .error {
    color: #e5a49b;
  }
</style>

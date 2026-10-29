<template>
  <main class="settings-page">
    <header class="page-header">
      <RouterLink class="back-link" to="/">Back to chat</RouterLink>
      <h1>Generation settings</h1>
      <p>Choose the local model and tune the response length and sampling behavior.</p>
    </header>

    <form v-if="settings" class="settings-form" @submit.prevent="save">
      <label class="field">
        <span>Ollama model</span>
        <div ref="modelPicker" class="model-picker" @keydown.esc.stop.prevent="closeModelMenu(true)">
          <button ref="modelTrigger" class="model-trigger" type="button" aria-label="Choose Ollama model"
            aria-haspopup="listbox" :aria-expanded="isModelMenuOpen" aria-controls="ollama-model-options"
            :disabled="loadingModels" @click="isModelMenuOpen = !isModelMenuOpen">
            <span class="model-name">{{ form.model_name }}</span>
            <span class="model-caret" aria-hidden="true"></span>
          </button>
          <div v-if="isModelMenuOpen" id="ollama-model-options" class="model-options" role="listbox"
            aria-label="Installed Ollama models">
            <button v-for="model in modelOptions" :key="model.name" class="model-option" type="button" role="option"
              :aria-selected="model.name === form.model_name" @click="selectModel(model.name)">
              <span class="model-option-name">{{ model.name }}</span>
              <span v-if="model.unavailable" class="model-note">currently selected</span>
              <span v-if="model.name === form.model_name" class="model-check" aria-hidden="true">✓</span>
            </button>
          </div>
        </div>
        <small v-if="modelError" class="field-note error">{{ modelError }}</small>
      </label>

      <label class="field">
        <span>Response length (tokens)</span>
        <input v-model.number="form.num_predict" type="number" min="1" max="32768" step="1" required />
        <small class="field-note">
          Maximum generated tokens, including reasoning. If the model returns no answer,
          try increasing this limit (for example, to 4096).
        </small>
      </label>

      <label class="field">
        <span>Temperature <output>{{ form.temperature.toFixed(2) }}</output></span>
        <input v-model.number="form.temperature" type="range" min="0" max="2" step="0.05" />
        <small class="field-note">Lower values are more focused; higher values are more varied.</small>
      </label>

      <label class="field">
        <span>Top-p <output>{{ form.top_p.toFixed(2) }}</output></span>
        <input v-model.number="form.top_p" type="range" min="0.01" max="1" step="0.01" />
        <small class="field-note">Limits sampling to the most likely token mass.</small>
      </label>

      <p v-if="error" class="notice error" role="alert">{{ error }}</p>
      <p v-if="saved" class="notice success" role="status">Settings saved.</p>
      <div class="actions">
        <button class="save-button" type="submit" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save settings' }}
        </button>
        <span v-if="loadingModels" class="field-note" role="status">Loading installed models...</span>
      </div>
    </form>
    <p v-else-if="error" class="notice error" role="alert">{{ error }}</p>
    <p v-else class="field-note" role="status">Loading settings...</p>
  </main>
</template>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
  import { getGenerationSettings, listAvailableModels, updateGenerationSettings } from '../services/settingsApi'
  import type { GenerationSettings } from '../types/roleplay'

  const settings = ref<GenerationSettings | null>(null)
  const form = reactive<GenerationSettings>({
    model_name: '',
    num_predict: 4096,
    temperature: 0.7,
    top_p: 0.9,
  })
  const models = ref<string[]>([])
  const isModelMenuOpen = ref(false)
  const modelPicker = ref<HTMLElement | null>(null)
  const modelTrigger = ref<HTMLButtonElement | null>(null)
  const modelOptions = computed(() => {
    const options = models.value.map((name) => ({ name, unavailable: false }))
    if (form.model_name && !models.value.includes(form.model_name)) {
      options.unshift({ name: form.model_name, unavailable: true })
    }
    return options
  })
  const loadingModels = ref(true)
  const saving = ref(false)
  const error = ref('')
  const modelError = ref('')
  const saved = ref(false)

  onMounted(async () => {
    document.addEventListener('pointerdown', closeOnOutsidePointer)
    try {
      const loadedSettings = await getGenerationSettings()
      settings.value = loadedSettings
      Object.assign(form, loadedSettings)
    } catch (cause: unknown) {
      error.value = cause instanceof Error ? cause.message : 'Could not load generation settings.'
    }

    try {
      models.value = await listAvailableModels()
    } catch (cause: unknown) {
      modelError.value = cause instanceof Error ? cause.message : 'Could not load installed Ollama models.'
    } finally {
      loadingModels.value = false
    }
  })

  onUnmounted(() => document.removeEventListener('pointerdown', closeOnOutsidePointer))

  function selectModel(modelName: string) {
    form.model_name = modelName
    saved.value = false
    isModelMenuOpen.value = false
  }

  function closeModelMenu(returnFocus = false) {
    isModelMenuOpen.value = false
    if (returnFocus) modelTrigger.value?.focus()
  }

  function closeOnOutsidePointer(event: PointerEvent) {
    if (event.target instanceof Node && !modelPicker.value?.contains(event.target)) {
      closeModelMenu()
    }
  }

  async function save() {
    if (!settings.value) return
    saving.value = true
    error.value = ''
    saved.value = false
    try {
      const updated = await updateGenerationSettings({ ...form })
      settings.value = updated
      Object.assign(form, updated)
      saved.value = true
    } catch (cause: unknown) {
      error.value = cause instanceof Error ? cause.message : 'Could not save generation settings.'
    } finally {
      saving.value = false
    }
  }
</script>

<style scoped>
  .settings-page {
    width: min(760px, 100%);
    height: 100%;
    margin: 0 auto;
    padding: 38px 32px;
    overflow-y: auto;
  }

  .page-header {
    margin-bottom: 28px;
  }

  .back-link {
    color: var(--color-gold);
    font-size: 12px;
    text-decoration: none;
  }

  h1 {
    margin: 16px 0 6px;
    color: #e5e5d9;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 32px;
    font-weight: 500;
  }

  .page-header p,
  .field-note {
    color: var(--color-muted);
    font-size: 12px;
    line-height: 1.6;
  }

  .settings-form {
    display: grid;
    gap: 21px;
    padding: 24px;
    border: 1px solid var(--color-line);
    border-radius: 12px;
    background: rgba(23, 33, 27, 0.82);
  }

  .field {
    display: grid;
    gap: 8px;
    color: #cdd2c9;
    font-size: 12px;
  }

  .field>span {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
  }

  output {
    color: var(--color-gold);
    font-variant-numeric: tabular-nums;
  }

  .field input[type='number'] {
    min-height: 40px;
    padding: 0 10px;
    border: 1px solid rgba(211, 218, 201, 0.14);
    border-radius: 7px;
    background: #111813;
    color: var(--color-text);
    font: inherit;
  }

  .model-picker {
    position: relative;
    min-width: 0;
  }

  .model-trigger {
    display: flex;
    width: 100%;
    min-height: 40px;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 0 10px;
    border: 1px solid rgba(211, 218, 201, 0.14);
    border-radius: 7px;
    background: #111813;
    color: var(--color-text);
    font: inherit;
    text-align: left;
    cursor: pointer;
    transition:
      border-color 150ms ease,
      background-color 150ms ease;
  }

  .model-trigger:hover:not(:disabled),
  .model-trigger[aria-expanded='true'] {
    border-color: rgba(196, 169, 110, 0.38);
  }

  .model-trigger:focus-visible {
    outline: 2px solid rgba(196, 169, 110, 0.3);
    outline-offset: 2px;
  }

  .model-trigger:disabled {
    cursor: wait;
    opacity: 0.65;
  }

  .model-name,
  .model-option-name {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .model-caret {
    width: 7px;
    height: 7px;
    flex: 0 0 auto;
    border-right: 1px solid #c4a96e;
    border-bottom: 1px solid #c4a96e;
    transform: translateY(-2px) rotate(45deg);
    transition: transform 150ms ease;
  }

  .model-trigger[aria-expanded='true'] .model-caret {
    transform: translateY(2px) rotate(225deg);
  }

  .model-options {
    position: absolute;
    z-index: 20;
    top: calc(100% + 7px);
    right: 0;
    left: 0;
    display: grid;
    max-height: min(300px, 50vh);
    gap: 3px;
    overflow-y: auto;
    padding: 6px;
    border: 1px solid rgba(144, 181, 151, 0.28);
    border-radius: 10px;
    background: rgba(12, 25, 18, 0.98);
    box-shadow:
      0 14px 32px rgba(0, 0, 0, 0.48),
      inset 0 1px 0 rgba(225, 238, 224, 0.035);
    backdrop-filter: blur(12px);
  }

  .model-option {
    display: flex;
    min-width: 0;
    min-height: 38px;
    align-items: center;
    gap: 10px;
    padding: 7px 10px;
    border: 1px solid transparent;
    border-radius: 6px;
    background: transparent;
    color: #c2cfc1;
    font: 500 11px/1.35 'DM Sans', 'Segoe UI', sans-serif;
    text-align: left;
    cursor: pointer;
    transition:
      background-color 120ms ease,
      border-color 120ms ease,
      color 120ms ease;
  }

  .model-option:hover,
  .model-option:focus-visible {
    border-color: rgba(143, 185, 150, 0.13);
    outline: none;
    background: rgba(52, 91, 62, 0.28);
    color: #f0f4ec;
  }

  .model-option[aria-selected='true'] {
    color: #e0eadc;
  }

  .model-note {
    flex: 0 0 auto;
    color: #89998a;
    font-size: 9px;
  }

  .model-check {
    flex: 0 0 auto;
    margin-left: auto;
    color: #c4a96e;
    font-size: 11px;
  }

  .field input[type='range'] {
    accent-color: var(--color-gold);
  }

  .field-note {
    margin: 0;
    font-size: 10px;
  }

  .notice {
    margin: 0;
    padding: 11px 13px;
    border-radius: 7px;
    font-size: 12px;
    line-height: 1.5;
  }

  .error {
    color: #e5a49b;
  }

  .notice.error {
    border: 1px solid rgba(229, 164, 155, 0.24);
    background: rgba(105, 50, 46, 0.2);
  }

  .notice.success {
    border: 1px solid rgba(126, 170, 131, 0.24);
    background: rgba(49, 86, 63, 0.22);
    color: #a6c7a8;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .save-button {
    min-height: 39px;
    padding: 0 14px;
    border: 1px solid rgba(196, 169, 110, 0.45);
    border-radius: 7px;
    background: rgba(60, 91, 65, 0.45);
    color: var(--color-text);
    font-size: 12px;
  }

  .save-button:disabled {
    cursor: wait;
    opacity: 0.6;
  }

  @media (prefers-reduced-motion: reduce) {

    .model-trigger,
    .model-caret,
    .model-option {
      transition: none;
    }
  }

  @media (max-width: 580px) {
    .settings-page {
      padding: 24px 16px;
    }

    .settings-form {
      padding: 18px;
    }
  }
</style>

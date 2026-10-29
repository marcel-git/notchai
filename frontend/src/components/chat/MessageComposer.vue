<template>
  <div class="composer-area">
    <form class="composer" @submit.prevent="emit('send')">
      <textarea ref="textarea" class="composer-input" :value="modelValue" rows="1" aria-label="Message"
        :placeholder="isSending ? 'Waiting for a reply...' : isDisabled ? 'Restoring conversation...' : 'Write something... du keck'"
        :disabled="isSending || isDisabled" @input="updateDraft"
        @keydown.enter.exact.prevent="emit('send')"></textarea>
      <div class="composer-footer">
        <div class="composer-tools"></div>
        <div class="composer-send-group">
          <span class="send-hint">Enter to send</span>
          <button class="send-button" type="submit" aria-label="Send message"
            :disabled="!modelValue.trim() || isSending || isDisabled">
            <BIcon icon="arrow-up" />
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
  import BIcon from './BIcon.vue'
  import { ref } from 'vue'

  defineProps<{
    modelValue: string
    isSending: boolean
    isDisabled: boolean
  }>()

  const emit = defineEmits<{
    'update:modelValue': [value: string]
    send: []
  }>()

  const textarea = ref<HTMLTextAreaElement | null>(null)

  function updateDraft(event: Event) {
    emit('update:modelValue', (event.target as HTMLTextAreaElement).value)
  }

  function focus() {
    textarea.value?.focus()
  }

  defineExpose({ focus })
</script>

<style scoped>
.composer-area {
  width: min(100% - 48px, 740px);
  margin: 0 auto;
  padding: 0 0 19px;
}

.composer {
  padding: 12px 13px 10px 16px;
  border: 1px solid rgba(175, 188, 169, 0.17);
  border-radius: 13px;
  background: linear-gradient(135deg, rgba(31, 43, 34, 0.97), rgba(25, 35, 28, 0.97));
  box-shadow: 0 12px 38px rgba(0, 0, 0, 0.12);
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease;
}

.composer:focus-within {
  border-color: rgba(196, 169, 110, 0.4);
  box-shadow:
    0 0 0 3px rgba(196, 169, 110, 0.035),
    0 12px 38px rgba(0, 0, 0, 0.12);
}

.composer-input {
  display: block;
  width: 100%;
  min-height: 43px;
  max-height: 160px;
  resize: vertical;
  padding: 4px 1px 7px;
  border: 0;
  outline: 0;
  background: transparent;
  color: #e3e6dc;
  font-size: 12px;
  line-height: 1.65;
}

.composer-input::placeholder {
  color: #8d998d;
}

.composer-input:focus-visible {
  outline: 0;
}

.composer-footer,
.composer-tools,
.composer-send-group {
  display: flex;
  align-items: center;
}

.composer-footer {
  justify-content: space-between;
}

.composer-tools {
  gap: 9px;
}

.composer-send-group {
  gap: 11px;
}

.send-hint {
  color: #707d72;
  font-size: 9px;
}

.send-button {
  display: grid;
  width: 31px;
  height: 31px;
  place-items: center;
  border: 1px solid rgba(198, 174, 118, 0.4);
  border-radius: 8px;
  background: linear-gradient(145deg, #c5ae78, #a78e58);
  color: #152019;
  transition:
    opacity 150ms ease,
    transform 150ms ease;
}

.send-button:not(:disabled):hover {
  transform: translateY(-1px);
  background: linear-gradient(145deg, #d4c08e, #b69d65);
}

.send-button:disabled {
  cursor: default;
  opacity: 0.42;
}

.send-button :deep(svg) {
  width: 16px;
  height: 16px;
}

@media (max-width: 580px) {
  .composer-area {
    width: calc(100% - 24px);
    padding-bottom: 12px;
  }

  .composer {
    padding: 10px 10px 8px 13px;
  }

  .composer-input {
    min-height: 39px;
  }

  .composer-tools {
    gap: 6px;
  }

  .send-hint {
    display: none;
  }
}
</style>

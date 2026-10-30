<template>
  <div class="message-thread">
    <article v-for="(message, index) in messages" :key="message.id ?? index" class="message-row" :class="[
      `message-${message.role}`,
      {
        'message-error': message.isError,
        'message-interrupted': message.isInterrupted,
        'message-superseded': message.isSuperseded,
      },
    ]">
      <div class="message-content">
        <div class="message-meta">
          <strong>{{ message.role === 'assistant' ? 'AI' : 'You' }}</strong>
          <span>{{ message.time }}</span>
        </div>

        <div v-if="message.content" class="message-markdown" v-html="renderedContents[index]"></div>
        <span
          v-if="message.isStreaming && message.isSummarizing"
          class="summarizing-indicator"
          role="status"
        >Summarizing conversation…</span>
        <span
          v-else-if="message.isStreaming"
          class="typing-indicator"
          aria-label="Generating response"
        ></span>
        <div v-if="message.isError" class="message-error-label">Response failed</div>
        <div v-else-if="message.isInterrupted" class="message-interrupted-label">Generation interrupted</div>

        <div v-if="!message.isSuperseded && !message.isStreaming" class="message-tools">
          <template v-if="message.role === 'assistant'">
            <button v-if="!message.isError && !message.isInterrupted" type="button" aria-label="Copy response"
              @click="copyResponse(message.content)">
              <BIcon icon="clipboard" />
            </button>
            <button v-if="message.id !== undefined && message.id === latestActiveMessageId" type="button"
              aria-label="Regenerate response" :disabled="isBusy" @click="regenerateMessage(message)">
              <BIcon icon="arrow-repeat" />
            </button>
          </template>
        </div>
        <p v-if="copyError" class="copy-error" role="alert">{{ copyError }}</p>
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
  import DOMPurify from 'dompurify'
  import MarkdownIt from 'markdown-it'
  import { computed, ref } from 'vue'
  import BIcon from './BIcon.vue'
  import type { ChatMessage } from '../../types/chat'

  const markdown = new MarkdownIt({
    breaks: true,
    html: false,
    linkify: false,
  })

  const props = defineProps<{
    messages: ChatMessage[]
    isBusy: boolean
  }>()

  const emit = defineEmits<{
    regenerate: [messageId: number]
  }>()

  const latestActiveMessageId = computed(() => {
    let latestId: number | undefined
    for (const message of props.messages) {
      if (
        !message.isSuperseded &&
        message.id !== undefined &&
        (latestId === undefined || message.id > latestId)
      ) {
        latestId = message.id
      }
    }
    return latestId
  })
  const renderedContents = computed(() =>
    props.messages.map((message) => DOMPurify.sanitize(markdown.render(message.content))),
  )
  const copyError = ref('')

  function regenerateMessage(message: ChatMessage) {
    if (message.id !== undefined) emit('regenerate', message.id)
  }

  async function copyResponse(content: string) {
    copyError.value = ''
    try {
      await navigator.clipboard.writeText(content)
    } catch {
      copyError.value = 'Could not copy the response to the clipboard.'
    }
  }
</script>

<style scoped>
  .message-thread {
    width: min(100% - 48px, 704px);
    flex: 0 0 auto;
    margin: 0 auto;
    padding: 39px 0 30px;
  }

  .message-row {
    display: flex;
    gap: 13px;
    margin: 0 0 30px;
  }

  .message-user {
    justify-content: flex-end;
  }

  .message-content {
    min-width: 0;
    max-width: 575px;
  }

  .message-error .message-markdown {
    color: #e5a49b;
  }

  .message-error-label,
  .message-interrupted-label,
  .message-superseded-label {
    margin-top: 6px;
    color: #bf8e83;
    font-size: 9px;
  }

  .message-interrupted .message-markdown {
    color: #c3b793;
  }

  .message-superseded {
    opacity: 0.62;
  }

  .message-superseded-label {
    color: #a59c82;
  }

  .branch-label {
    color: #b9a16a !important;
    font-size: 9px !important;
  }

  .typing-indicator {
    display: block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #c5ae78;
    animation: typing-pulse 900ms ease-in-out infinite alternate;
  }

  .summarizing-indicator {
    display: inline-block;
    color: var(--color-muted);
    font-size: 10px;
    font-style: italic;
  }

  @keyframes typing-pulse {
    from {
      opacity: 0.35;
      transform: scale(0.8);
    }

    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  .message-user .message-content {
    max-width: 515px;
    padding: 13px 16px 14px;
    border: 1px solid rgba(133, 158, 129, 0.13);
    border-radius: 12px 4px 12px 12px;
    background: linear-gradient(135deg, rgba(46, 67, 49, 0.64), rgba(33, 48, 37, 0.67));
  }

  .message-meta {
    display: flex;
    align-items: baseline;
    gap: 9px;
    margin-bottom: 8px;
  }

  .message-meta strong {
    color: #d9dfd4;
    font-size: 11px;
    font-weight: 600;
  }

  .message-user .message-meta strong {
    color: #d9d5c4;
  }

  .message-meta>span {
    color: #79847a;
    font-size: 9px;
  }

  .message-markdown {
    color: #c3c9c0;
    font-size: 12px;
    line-height: 1.82;
    overflow-wrap: anywhere;
  }

  .message-markdown :deep(:first-child) {
    margin-top: 0;
  }

  .message-markdown :deep(:last-child) {
    margin-bottom: 0;
  }

  .message-markdown :deep(p) {
    margin: 0;
    white-space: pre-wrap;
  }

  .message-markdown :deep(em) {
    font-family: Georgia, serif;
    font-style: italic;
  }

  .message-markdown :deep(p + p),
  .message-markdown :deep(ul),
  .message-markdown :deep(ol),
  .message-markdown :deep(blockquote),
  .message-markdown :deep(pre),
  .message-markdown :deep(table) {
    margin-top: 0.75em;
  }

  .message-markdown :deep(h1),
  .message-markdown :deep(h2),
  .message-markdown :deep(h3),
  .message-markdown :deep(h4),
  .message-markdown :deep(h5),
  .message-markdown :deep(h6) {
    margin: 1em 0 0.45em;
    color: #e0e4d9;
    font-size: 1.12em;
    font-weight: 600;
    line-height: 1.4;
  }

  .message-markdown :deep(ul),
  .message-markdown :deep(ol) {
    padding-left: 1.6em;
  }

  .message-markdown :deep(blockquote) {
    padding-left: 0.85em;
    border-left: 2px solid var(--color-gold);
    color: #aeb6aa;
  }

  .message-markdown :deep(code) {
    padding: 0.12em 0.35em;
    border-radius: 4px;
    background: rgba(5, 10, 7, 0.42);
    color: #d9c89b;
    font-family: Consolas, 'Courier New', monospace;
    font-size: 0.92em;
  }

  .message-markdown :deep(pre) {
    padding: 11px 12px;
    overflow-x: auto;
    border: 1px solid rgba(211, 218, 201, 0.1);
    border-radius: 7px;
    background: rgba(5, 10, 7, 0.48);
    white-space: pre;
  }

  .message-markdown :deep(pre code) {
    padding: 0;
    background: transparent;
    color: inherit;
    font-size: 0.95em;
  }

  .message-markdown :deep(a) {
    color: #d0b879;
    text-decoration: underline;
    text-underline-offset: 2px;
  }

  .message-markdown :deep(table) {
    display: block;
    max-width: 100%;
    overflow-x: auto;
    border-collapse: collapse;
  }

  .message-markdown :deep(th),
  .message-markdown :deep(td) {
    padding: 6px 9px;
    border: 1px solid rgba(211, 218, 201, 0.18);
    text-align: left;
  }

  .message-user .message-markdown {
    color: #d5dbd0;
    line-height: 1.7;
  }

  .message-tools,
  .edit-actions {
    display: flex;
    gap: 4px;
    margin-top: 10px;
  }

  .message-tools button,
  .edit-actions button {
    display: grid;
    min-width: 26px;
    height: 27px;
    place-items: center;
    padding: 0 7px;
    border-radius: 5px;
    background: transparent;
    color: #818d82;
    font-size: 10px;
  }

  .message-tools button:hover,
  .edit-actions button:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #d7dacf;
  }

  .message-tools button:disabled,
  .edit-actions button:disabled {
    cursor: wait;
    opacity: 0.5;
  }

  .message-tools :deep(svg) {
    width: 13px;
    height: 13px;
  }

  .copy-error {
    margin-top: 6px !important;
    color: #e5a49b !important;
    font-size: 10px !important;
  }

  @media (max-width: 580px) {
    .message-thread {
      width: calc(100% - 30px);
      padding-top: 25px;
    }

    .message-row {
      gap: 9px;
      margin-bottom: 24px;
    }

    .message-markdown {
      font-size: 11px;
    }
  }
</style>

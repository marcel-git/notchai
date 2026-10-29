<template>
  <header class="topbar">
    <div class="topbar-main">
      <button class="icon-button menu-button" aria-label="Open conversation menu" @click="emit('openSidebar')">
        <BIcon icon="list" />
      </button>
      <div
        v-if="conversationId"
        class="context-meter"
        :class="{
          'context-meter-warning': usagePercent >= 80,
          'context-meter-critical': usagePercent >= 95,
        }"
        role="img"
        tabindex="0"
        :aria-label="contextDescription"
        aria-describedby="context-meter-tooltip"
      >
        <span class="context-prefix">CTX</span>
        <span class="context-value">
          {{ contextMeter?.runtime_context_length ? `${usagePercent}%` : '--' }}
        </span>
        <div class="context-track" aria-hidden="true">
          <span
            v-for="section in displayedSections"
            :key="section.key"
            class="context-segment"
            :class="`context-segment-${section.role}`"
            :style="{ width: `${section.width}%` }"
          ></span>
        </div>
        <div id="context-meter-tooltip" class="context-tooltip" role="tooltip">
          <div class="tooltip-heading">
            <strong>Context breakdown</strong>
            <span v-if="contextMeter?.runtime_context_length">
              ~{{ formatNumber(totalEstimatedTokens) }} /
              {{ formatNumber(contextMeter.runtime_context_length) }}
            </span>
          </div>
          <div class="tooltip-row">
            <span>System prompt</span>
            <span>{{ formatEstimate(systemPromptTokens) }}</span>
          </div>
          <div class="tooltip-row">
            <span>Conversation history</span>
            <span>{{ formatEstimate(historyTokens) }}</span>
          </div>
          <div class="tooltip-detail">
            <span>User messages</span>
            <span>{{ formatEstimate(userHistoryTokens) }}</span>
          </div>
          <div class="tooltip-detail">
            <span>Assistant messages</span>
            <span>{{ formatEstimate(assistantHistoryTokens) }}</span>
          </div>
          <div class="tooltip-row">
            <span>Current user input</span>
            <span>{{ formatEstimate(draftTokens) }}</span>
          </div>
          <div class="tooltip-row">
            <span>Tools / functions</span>
            <span>None sent</span>
          </div>
          <p v-if="contextMeter?.context_note" class="tooltip-note">
            {{ contextMeter.context_note }}
          </p>
          <p v-else class="tooltip-note">
            No separate cross-conversation memory is included. Counts are rough estimates and
            exclude model message-formatting overhead.
          </p>
          <p v-if="contextError" class="tooltip-note tooltip-error">{{ contextError }}</p>
        </div>
      </div>
      <!-- <strong v-if="conversationId" class="conversation-title">{{ title }}</strong> -->
      <div v-if="characterName || personaName" class="role-labels">
        <span><strong>Character:</strong> {{ characterName || 'Unavailable' }}</span>
        <span><strong>Your persona:</strong> {{ personaName || 'Unavailable' }}</span>
      </div>
      <div class="conversation-tools">
        <template v-if="conversationId">
          <button class="icon-button" aria-label="Rename conversation" :disabled="isBusy" @click="emit('rename')">
            <BIcon icon="pencil" />
          </button>
          <button class="icon-button" aria-label="Inspect assembled prompt" :disabled="isBusy"
            @click="emit('inspectPrompt')">
            <BIcon icon="search" />
          </button>
          <button class="icon-button delete-button" aria-label="Delete conversation" :disabled="isBusy"
            @click="emit('delete')">
            <BIcon icon="trash" />
          </button>
        </template>
        <button
          ref="sensoryButton"
          class="icon-button sensory-button"
          type="button"
          aria-label="Open sensory board"
          title="Sensory board"
          @click="emit('openSensoryBoard')"
        >
          <BIcon icon="hand-index-thumb" />
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
  import { computed, ref } from 'vue'
  import type { ContextMeterData } from '../../types/roleplay'
  import BIcon from './BIcon.vue'

  const props = defineProps<{
    conversationId: string | null
    title: string
    characterName?: string
    personaName?: string
    isBusy: boolean
    contextMeter: ContextMeterData | null
    contextDraft: string
    contextError: string
  }>()
  const sensoryButton = ref<HTMLButtonElement | null>(null)

  const emit = defineEmits<{
    openSidebar: []
    rename: []
    delete: []
    inspectPrompt: []
    openSensoryBoard: []
  }>()

  function focusSensoryButton() {
    sensoryButton.value?.focus()
  }

  defineExpose({ focusSensoryButton })

  type DisplayedSection = {
    key: string
    label: string
    role: ContextMeterData['sections'][number]['role'] | 'draft'
    estimated_tokens: number
    width: number
  }

  const draftTokens = computed(() => estimateTokens(props.contextDraft.trim()))
  const totalEstimatedTokens = computed(
    () => (props.contextMeter?.estimated_tokens_total ?? 0) + draftTokens.value,
  )
  const systemPromptTokens = computed(() =>
    sumSections((section) => section.role === 'system'),
  )
  const userHistoryTokens = computed(() =>
    sumSections((section) => section.role === 'user'),
  )
  const assistantHistoryTokens = computed(() =>
    sumSections((section) => section.role === 'assistant'),
  )
  const historyTokens = computed(
    () => userHistoryTokens.value + assistantHistoryTokens.value,
  )
  const usagePercent = computed(() => {
    const limit = props.contextMeter?.runtime_context_length
    return limit ? Math.min(999, Math.round((totalEstimatedTokens.value / limit) * 100)) : 0
  })
  const displayedSections = computed<DisplayedSection[]>(() => {
    const limit = props.contextMeter?.runtime_context_length
    if (!limit || !props.contextMeter) return []
    const sections: Omit<DisplayedSection, 'width'>[] = props.contextMeter.sections.map((section, index) => ({
      key: `${section.role}-${index}`,
      label: section.label,
      role: section.role,
      estimated_tokens: section.estimated_tokens,
    }))
    if (draftTokens.value) {
      sections.push({
        key: 'draft',
        label: 'Draft message',
        role: 'draft',
        estimated_tokens: draftTokens.value,
      })
    }

    let remainingWidth = 100
    return sections.map((section) => {
      const width = Math.min(
        remainingWidth,
        (section.estimated_tokens / limit) * 100,
      )
      remainingWidth -= width
      return { ...section, width }
    })
  })
  const contextDescription = computed(() => {
    if (!props.contextMeter) {
      return props.contextError || 'Context estimate is loading.'
    }
    const sections = displayedSections.value
      .map(
        (section) =>
          `${section.label}: approximately ${formatNumber(section.estimated_tokens)} tokens`,
      )
      .join('; ')
    const limit = props.contextMeter.runtime_context_length
    const summary = limit
      ? `Approximately ${formatNumber(totalEstimatedTokens.value)} of ${formatNumber(limit)} tokens (${usagePercent.value}%).`
      : `Approximately ${formatNumber(totalEstimatedTokens.value)} tokens; runtime limit unavailable.`
    return [summary, sections, props.contextMeter.context_note].filter(Boolean).join(' ')
  })

  function estimateTokens(content: string) {
    return Math.ceil(content.length / 4)
  }

  function sumSections(matches: (section: ContextMeterData['sections'][number]) => boolean) {
    return props.contextMeter?.sections
      .filter(matches)
      .reduce((total, section) => total + section.estimated_tokens, 0) ?? 0
  }

  function formatNumber(value: number) {
    return new Intl.NumberFormat().format(value)
  }

  function formatEstimate(value: number) {
    return `~${formatNumber(value)} tokens`
  }
</script>

<style scoped>
  .topbar {
    z-index: 1;
    display: flex;
    height: 65px;
    min-height: 65px;
    align-items: center;
    justify-content: space-between;
    padding: 0 29px;
    border-bottom: 1px solid var(--color-line);
    background: rgba(17, 24, 19, 0.72);
  }

  .topbar-main {
    display: flex;
    min-width: 0;
    flex: 1;
    min-height: 38px;
    align-items: center;
    justify-content: space-between;
  }

  .role-labels {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 20px;
    margin-left: auto;
    color: #9fa89f;
    font-size: 10px;
  }

  .conversation-title {
    overflow: hidden;
    max-width: 240px;
    color: #e5e5d9;
    font-size: 12px;
    font-weight: 500;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .conversation-tools {
    display: flex;
    align-items: center;
    gap: 2px;
    margin-left: 12px;
  }

  .conversation-tools :deep(svg) {
    width: 14px;
    height: 14px;
  }

  .conversation-tools button:disabled {
    cursor: wait;
    opacity: 0.45;
  }

  .delete-button:hover {
    color: #e5a49b;
  }

  .sensory-button:hover {
    color: var(--color-gold);
  }

  .role-labels strong {
    color: #cbb37d;
    font-weight: 500;
  }

  .context-meter {
    position: relative;
    display: flex;
    width: 118px;
    flex: 0 0 118px;
    align-items: center;
    gap: 6px;
    margin-right: 14px;
    color: rgba(166, 178, 165, 0.58);
    font-size: 8px;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.025em;
    line-height: 1;
  }

  .context-meter:focus-visible {
    outline: 1px solid rgba(196, 169, 110, 0.42);
    outline-offset: 4px;
  }

  .context-prefix {
    color: rgba(196, 169, 110, 0.68);
    font-size: 7px;
    font-weight: 600;
    letter-spacing: 0.08em;
  }

  .context-value {
    width: 24px;
    text-align: right;
  }

  .context-track {
    display: flex;
    width: 56px;
    height: 4px;
    overflow: hidden;
    border-radius: 4px;
    background: rgba(211, 218, 201, 0.1);
  }

  .context-segment {
    height: 100%;
    min-width: 0;
    transition: width 180ms ease;
  }

  .context-segment-system {
    background: #c4a96e;
  }

  .context-segment-user {
    background: #719574;
  }

  .context-segment-assistant {
    background: #477354;
  }

  .context-segment-draft {
    background: #d3bd85;
  }

  .context-meter-warning .context-value {
    color: rgba(196, 169, 110, 0.9);
  }

  .context-meter-critical .context-value {
    color: #e5a49b;
  }

  .context-tooltip {
    position: absolute;
    z-index: 20;
    top: calc(100% + 9px);
    left: 0;
    display: none;
    width: 238px;
    padding: 11px 12px;
    border: 1px solid rgba(144, 181, 151, 0.26);
    border-radius: 8px;
    background: rgba(12, 25, 18, 0.98);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.42);
    color: #c2cfc1;
    font-size: 10px;
    font-variant-numeric: tabular-nums;
    line-height: 1.5;
    letter-spacing: normal;
    white-space: normal;
    opacity: 0;
    pointer-events: none;
    transform: translateY(-3px);
    transition:
      opacity 120ms ease,
      transform 120ms ease;
  }

  .context-meter:hover .context-tooltip,
  .context-meter:focus .context-tooltip,
  .context-meter:focus-within .context-tooltip {
    display: block;
    opacity: 1;
    transform: translateY(0);
  }

  .tooltip-heading,
  .tooltip-row,
  .tooltip-detail {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
  }

  .tooltip-heading {
    margin-bottom: 7px;
    color: #e0e8dc;
  }

  .tooltip-heading span {
    color: #a7b0a5;
  }

  .tooltip-row {
    padding: 2px 0;
  }

  .tooltip-row > span:last-child,
  .tooltip-detail > span:last-child {
    color: #d3ddcf;
    white-space: nowrap;
  }

  .tooltip-detail {
    padding: 1px 0 1px 10px;
    color: #89998a;
    font-size: 9px;
  }

  .tooltip-note {
    margin: 7px 0 0;
    color: #89998a;
    font-size: 9px;
    line-height: 1.4;
  }

  .tooltip-error {
    color: #e5a49b;
  }

  .menu-button {
    display: none;
  }

  .menu-button :deep(svg) {
    width: 17px;
    height: 17px;
  }

  @media (max-width: 820px) {
    .topbar {
      justify-content: flex-start;
      gap: 10px;
      padding: 0 19px;
    }

    .topbar-main {
      justify-content: flex-start;
      gap: 10px;
    }

    .role-labels {
      gap: 8px;
      margin-left: auto;
    }

    .conversation-title {
      max-width: 130px;
    }

    .conversation-tools {
      margin-left: 4px;
    }

    .menu-button {
      display: grid;
    }

  }

  @media (max-width: 580px) {
    .topbar {
      height: 58px;
      min-height: 58px;
      gap: 7px;
      padding: 0 13px;
    }

    .topbar-main {
      min-height: 34px;
      gap: 7px;
    }

    .role-labels {
      min-width: 0;
      align-items: center;
      gap: 8px;
      font-size: 8px;
    }

    .context-meter {
      width: 105px;
      flex-basis: 105px;
      gap: 5px;
      margin-right: 0;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .context-segment,
    .context-tooltip {
      transition: none;
    }
  }
</style>
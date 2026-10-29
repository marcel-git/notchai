<template>
  <header class="topbar">
    <button class="icon-button menu-button" aria-label="Open conversation menu" @click="emit('openSidebar')">
      <BIcon icon="list" />
    </button>
    <!-- <strong v-if="conversationId" class="conversation-title">{{ title }}</strong> -->
    <div v-if="characterName || personaName" class="role-labels">
      <span><strong>Character:</strong> {{ characterName || 'Unavailable' }}</span>
      <span><strong>Your persona:</strong> {{ personaName || 'Unavailable' }}</span>
    </div>
    <div v-if="conversationId" class="conversation-tools">
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
    </div>
  </header>
</template>

<script setup lang="ts">
  import BIcon from './BIcon.vue'

  defineProps<{
    conversationId: string | null
    title: string
    characterName?: string
    personaName?: string
    isBusy: boolean
  }>()

  const emit = defineEmits<{
    openSidebar: []
    rename: []
    delete: []
    inspectPrompt: []
  }>()
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

  .role-labels strong {
    color: #cbb37d;
    font-weight: 500;
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
      gap: 12px;
      padding: 0 19px;
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
      padding: 0 13px;
    }
  }
</style>
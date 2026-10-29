<template>
  <button v-if="isOpen" class="sidebar-scrim" aria-label="Close conversation menu" @click="emit('close')"></button>

  <aside class="sidebar" :class="{ 'sidebar-open': isOpen }">
    <div class="brand">
      <div class="brand-copy">
        <span class="brand-name">Definetly Not CHAI</span>
        <span class="brand-caption">Please don't sue me :3</span>
      </div>
      <button class="icon-button sidebar-close" aria-label="Close menu" @click="emit('close')">
        <BIcon icon="x" />
      </button>
    </div>

    <button class="new-chat-button" @click="emit('newChat')">
      <BIcon icon="plus" />
      <span>New conversation</span>
    </button>

    <div class="sidebar-section">
      <p class="section-label">MENU</p>
      <RouterLink class="library-item" to="/personas" @click="emit('close')">
        <BIcon icon="file-person" />
        <span>Personas</span>
      </RouterLink>
      <RouterLink class="library-item" to="/characters" @click="emit('close')">
        <BIcon icon="people" />
        <span>Characters</span>
      </RouterLink>
      <RouterLink class="library-item" to="/settings" @click="emit('close')">
        <BIcon icon="sliders" />
        <span>Generation settings</span>
      </RouterLink>
    </div>

    <div class="history">
      <div class="history-heading">
        <p class="section-label">CHATS</p>
      </div>
      <nav class="conversation-list" aria-label="Recent conversations">
        <button v-for="conversation in conversations" :key="conversation.id" class="conversation-link"
          :class="{ 'conversation-active': activeConversationId === conversation.id }"
          @click="emit('selectConversation', conversation.id)">
          <span class="conversation-dot"></span>
          <span class="conversation-title">{{ conversation.title }}</span>
          <span v-if="activeConversationId === conversation.id" class="active-mark"></span>
        </button>
      </nav>
    </div>
  </aside>
</template>

<script setup lang="ts">
  import BIcon from './BIcon.vue'
  import type { Conversation } from '../../types/chat'
  import { RouterLink } from 'vue-router'

  defineProps<{
    conversations: Conversation[]
    activeConversationId: string | null
    isOpen: boolean
  }>()

  const emit = defineEmits<{
    close: []
    newChat: []
    selectConversation: [id: string]
  }>()
</script>

<style scoped>
  .sidebar {
    z-index: 3;
    display: flex;
    width: 278px;
    min-width: 278px;
    flex-direction: column;
    padding: 25px 15px 15px;
    border-right: 1px solid var(--color-line);
    background: #141c16;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 0 7px;
  }

  .brand-copy {
    display: flex;
    min-width: 0;
    flex-direction: column;
  }

  .brand-name {
    color: #e6dfc8;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.13em;
  }

  .brand-caption {
    margin-top: 2px;
    color: #8d978d;
    font-size: 10px;
    letter-spacing: 0.04em;
  }

  .icon-button :deep(svg),
  .new-chat-button :deep(svg),
  .library-item :deep(svg) {
    width: 17px;
    height: 17px;
  }

  .sidebar-close {
    display: none;
    margin-left: auto;
  }

  .new-chat-button {
    display: flex;
    align-items: center;
    height: 42px;
    gap: 10px;
    margin: 30px 1px 28px;
    padding: 0 11px;
    border: 1px solid rgba(196, 169, 110, 0.28);
    border-radius: 8px;
    background: linear-gradient(110deg, rgba(60, 91, 65, 0.3), rgba(39, 59, 43, 0.22));
    color: #e8e5d7;
    font-size: 12px;
    font-weight: 500;
    text-align: left;
    transition:
      border-color 160ms ease,
      background 160ms ease;
  }

  .new-chat-button:hover {
    border-color: rgba(196, 169, 110, 0.55);
    background: rgba(68, 99, 72, 0.34);
  }

  .new-chat-button :deep(svg) {
    width: 16px;
    color: #cbb37d;
  }

  .sidebar-section {
    padding: 0 2px;
  }

  .section-label {
    margin: 0;
    color: #78847a;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.16em;
  }

  .sidebar-section>.section-label {
    padding: 0 9px 10px;
  }

  .library-item {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 11px;
    padding: 9px 10px;
    border-radius: 7px;
    background: transparent;
    color: #a9b0a7;
    font-size: 11px;
    text-align: left;
    text-decoration: none;
    transition:
      background 150ms ease,
      color 150ms ease;
  }

  .library-item:hover {
    background: rgba(255, 255, 255, 0.045);
    color: #eceee4;
  }

  .library-item :deep(svg) {
    width: 15px;
    height: 15px;
    color: #859385;
  }

  .count {
    margin-left: auto;
    color: #879087;
    font-size: 10px;
  }

  .history {
    min-height: 0;
    flex: 1;
    margin-top: 31px;
    overflow: hidden;
  }

  .history-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 4px 7px 11px;
  }

  .history-search {
    width: 28px;
    height: 28px;
  }

  .history-search :deep(svg) {
    width: 15px;
    height: 15px;
  }

  .conversation-list {
    display: grid;
    max-height: 100%;
    gap: 3px;
    overflow-y: auto;
  }

  .conversation-link {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 10px;
    padding: 10px;
    border-radius: 7px;
    background: transparent;
    color: #9fa89f;
    font-size: 11px;
    text-align: left;
    transition:
      background 150ms ease,
      color 150ms ease;
  }

  .conversation-link:hover {
    background: rgba(255, 255, 255, 0.045);
    color: #e7eae0;
  }

  .conversation-active {
    background: #202c23;
    color: #eceee4;
  }

  .conversation-active:hover {
    background: #253329;
  }

  .conversation-dot {
    width: 5px;
    height: 5px;
    flex: 0 0 auto;
    border-radius: 50%;
    background: #708a70;
    opacity: 0.7;
  }

  .conversation-active .conversation-dot {
    background: #c6ad72;
    opacity: 1;
    box-shadow: 0 0 8px rgba(196, 169, 110, 0.35);
  }

  .conversation-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .active-mark {
    width: 3px;
    height: 15px;
    flex: 0 0 auto;
    margin-left: auto;
    border-radius: 4px;
    background: #b99c5f;
  }

  .sidebar-scrim {
    display: none;
  }

  @media (max-width: 820px) {
    .sidebar {
      position: fixed;
      inset: 0 auto 0 0;
      width: min(290px, calc(100vw - 54px));
      min-width: 0;
      transform: translateX(-102%);
      transition:
        transform 220ms ease,
        box-shadow 220ms ease;
      box-shadow: 18px 0 48px rgba(0, 0, 0, 0.28);
    }

    .sidebar-open {
      transform: translateX(0);
    }

    .sidebar-close {
      display: grid;
    }

    .sidebar-scrim {
      position: fixed;
      z-index: 2;
      inset: 0;
      display: block;
      background: rgba(4, 8, 5, 0.63);
      backdrop-filter: blur(2px);
    }
  }
</style>
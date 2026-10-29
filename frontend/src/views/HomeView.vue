<template>
  <main class="chat-shell">
    <ChatSidebar :conversations="conversations" :active-conversation-id="activeConversationId" :is-open="isSidebarOpen"
      @close="isSidebarOpen = false" @new-chat="startNewChat" @select-conversation="selectConversation" />

    <section class="chat-panel">
      <ChatHeader :conversation-id="activeConversationId" :title="activeConversation?.title ?? ''"
        :character-name="activeCharacterName" :persona-name="activePersonaName" :is-busy="isSending"
        @open-sidebar="isSidebarOpen = true" @rename="renameActiveConversation" @delete="deleteActiveConversation"
        @inspect-prompt="inspectPrompt" />

      <div ref="messageList" class="chat-scroll">
        <ConversationStart v-if="isStartVisible" :characters="characters" :personas="personas"
          :loading="isLoading || areProfilesLoading" :is-starting="isStartingConversation" :error="profileError"
          @start="startConversation" />
        <MessageThread v-else-if="activeConversation && activeConversation.messages.length > 0"
          :messages="activeConversation.messages" :is-busy="isSending" @regenerate="regenerateMessage" />
        <WelcomeScreen v-else-if="!isLoading" />
        <p v-if="loadError" class="chat-status chat-status-error" role="alert">{{ loadError }}</p>
        <p v-else-if="isLoading" class="chat-status" role="status">Restoring conversations...</p>
      </div>

      <MessageComposer v-if="!isStartVisible" ref="composer" v-model="draft" :is-sending="isSending"
        :is-disabled="isLoading" @send="sendMessage" />
    </section>
    <PromptInspector :open="isPromptInspectorOpen" :loading="isPromptLoading" :error="promptError"
      :inspection="promptInspection" :editable="isPromptEditable" :saving="isPromptSaving"
      @close="closePromptInspector" @confirm="confirmConversationStart" />
  </main>
</template>

<script setup lang="ts">
  import { computed, nextTick, onMounted, ref, watch } from 'vue'
  import ConversationStart from '../components/chat/ConversationStart.vue'
  import ChatHeader from '../components/chat/ChatHeader.vue'
  import ChatSidebar from '../components/chat/ChatSidebar.vue'
  import MessageComposer from '../components/chat/MessageComposer.vue'
  import MessageThread from '../components/chat/MessageThread.vue'
  import PromptInspector from '../components/chat/PromptInspector.vue'
  import WelcomeScreen from '../components/chat/WelcomeScreen.vue'
  import { useChat } from '../composables/useChat'
  import { getPromptInspection, getPromptPreview } from '../services/chatApi'
  import { listCharacters, listPersonas } from '../services/profileApi'
  import type { CharacterProfile, PersonaProfile } from '../types/profiles'
  import type { PromptInspection as PromptInspectionData } from '../types/roleplay'

  const {
    activeConversation,
    activeConversationId,
    conversations,
    isLoading,
    isSending,
    loadError,
    deleteConversation,
    regenerateMessage: regenerateReply,
    renameConversation,
    selectConversation: selectChat,
    sendMessage: addMessage,
    startNewChat: createChat,
  } = useChat()

  const draft = ref('')
  const isSidebarOpen = ref(false)
  const messageList = ref<HTMLElement | null>(null)
  const composer = ref<{ focus: () => void } | null>(null)
  const isStartFlowOpen = ref(false)
  const isStartingConversation = ref(false)
  const areProfilesLoading = ref(true)
  const characters = ref<CharacterProfile[]>([])
  const personas = ref<PersonaProfile[]>([])
  const profileError = ref('')
  const isPromptInspectorOpen = ref(false)
  const isPromptLoading = ref(false)
  const promptError = ref('')
  const promptInspection = ref<PromptInspectionData | null>(null)
  const isPromptEditable = ref(false)
  const isPromptSaving = ref(false)
  const pendingConversationStart = ref<{ characterId: string; personaId: string | null } | null>(null)
  const isStartVisible = computed(
    () => !isLoading.value && (!activeConversation.value || isStartFlowOpen.value),
  )
  const activeCharacterName = computed(() =>
    characters.value.find((character) => character.id === activeConversation.value?.character_id)?.name,
  )
  const activePersonaName = computed(() =>
    personas.value.find((persona) => persona.id === activeConversation.value?.persona_id)?.name,
  )

  onMounted(async () => {
    try {
      const [loadedCharacters, loadedPersonas] = await Promise.all([
        listCharacters(),
        listPersonas(),
      ])
      characters.value = loadedCharacters
      personas.value = loadedPersonas
    } catch (error: unknown) {
      profileError.value = error instanceof Error ? error.message : 'Could not load profiles.'
    } finally {
      areProfilesLoading.value = false
    }
  })

  function scrollToBottom() {
    messageList.value?.scrollTo({ top: messageList.value.scrollHeight, behavior: 'smooth' })
  }

  watch(
    [
      activeConversationId,
      () => activeConversation.value?.messages.at(-1)?.content,
    ],
    () => nextTick(scrollToBottom),
    { flush: 'post' },
  )

  function selectConversation(id: string) {
    selectChat(id)
    isStartFlowOpen.value = false
    isSidebarOpen.value = false
  }

  function startNewChat() {
    isStartFlowOpen.value = true
    isSidebarOpen.value = false
  }

  function renameActiveConversation() {
    const conversation = activeConversation.value
    if (!conversation || isSending.value) return
    const title = window.prompt('Conversation name', conversation.title)
    if (title === null) return
    const trimmedTitle = title.trim()
    if (!trimmedTitle) {
      loadError.value = 'Conversation name must not be blank.'
      return
    }
    void renameConversation(trimmedTitle)
  }

  function deleteActiveConversation() {
    const conversation = activeConversation.value
    if (!conversation || isSending.value) return
    if (window.confirm(`Delete "${conversation.title}" and its messages?`)) {
      void deleteConversation(conversation.id)
    }
  }

  async function inspectPrompt() {
    const conversationId = activeConversationId.value
    if (!conversationId) return
    isPromptEditable.value = false
    pendingConversationStart.value = null
    isPromptInspectorOpen.value = true
    isPromptLoading.value = true
    promptError.value = ''
    promptInspection.value = null
    try {
      promptInspection.value = await getPromptInspection(conversationId)
    } catch (error: unknown) {
      promptError.value = error instanceof Error ? error.message : 'Could not inspect this prompt.'
    } finally {
      isPromptLoading.value = false
    }
  }

  function regenerateMessage(messageId: number) {
    regenerateReply(messageId)
  }

  async function startConversation(characterId: string, personaId: string | null) {
    pendingConversationStart.value = { characterId, personaId }
    isPromptEditable.value = true
    isPromptInspectorOpen.value = true
    isPromptLoading.value = true
    promptError.value = ''
    promptInspection.value = null
    isStartingConversation.value = true
    try {
      promptInspection.value = await getPromptPreview(characterId, personaId)
    } catch (error: unknown) {
      promptError.value =
        error instanceof Error ? error.message : 'Could not build the system prompt preview.'
    } finally {
      isPromptLoading.value = false
      isStartingConversation.value = false
    }
  }

  async function confirmConversationStart(systemPrompt: string) {
    const pending = pendingConversationStart.value
    if (!pending || isPromptSaving.value) return
    isPromptSaving.value = true
    promptError.value = ''
    try {
      if (await createChat(pending.characterId, pending.personaId, systemPrompt)) {
        isStartFlowOpen.value = false
        isPromptSaving.value = false
        closePromptInspector()
        nextTick(() => composer.value?.focus())
      } else {
        promptError.value = loadError.value || 'Could not start this conversation.'
      }
    } finally {
      isPromptSaving.value = false
    }
  }

  function closePromptInspector() {
    if (isPromptSaving.value) return
    isPromptInspectorOpen.value = false
    isPromptEditable.value = false
    pendingConversationStart.value = null
  }

  function sendMessage() {
    if (addMessage(draft.value)) {
      draft.value = ''
      nextTick(scrollToBottom)
    }
  }
</script>

<style scoped>
  .chat-shell {
    display: flex;
    width: 100%;
    height: 100vh;
    height: 100dvh;
    min-height: 0;
    overflow: hidden;
    background:
      radial-gradient(ellipse at 73% 51%, rgba(48, 74, 54, 0.08), transparent 38%),
      var(--color-bg);
  }

  .chat-panel {
    position: relative;
    display: flex;
    min-width: 0;
    height: 100%;
    min-height: 0;
    flex: 1;
    flex-direction: column;
    overflow: hidden;
  }

  .chat-scroll {
    display: flex;
    min-height: 0;
    flex: 1;
    flex-direction: column;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
    scrollbar-color: rgba(163, 175, 160, 0.18) transparent;
    scrollbar-width: thin;
  }

  .chat-status {
    width: min(100% - 48px, 704px);
    margin: 24px auto 0;
    color: #9fa89f;
    font-size: 12px;
  }

  .chat-status-error {
    color: #e5a49b;
  }
</style>

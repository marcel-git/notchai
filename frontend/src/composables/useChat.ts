import { computed, reactive, ref } from 'vue'
import {
  createConversation as createConversationRequest,
  deleteConversation as deleteConversationRequest,
  getConversation,
  listConversations,
  renameConversation as renameConversationRequest,
  streamChatReply,
  streamRegeneratedReply,
} from '../services/chatApi'
import type { ChatMessage, Conversation } from '../types/chat'

export function useChat() {
  const conversations = ref<Conversation[]>([])
  const activeConversationId = ref<string | null>(null)
  const pendingConversationIds = ref(new Set<string>())
  const guidanceSavedCount = ref(0)
  const loadedConversationIds = new Set<string>()
  const isLoading = ref(true)
  const loadError = ref('')
  const activeConversation = computed(() =>
    conversations.value.find((conversation) => conversation.id === activeConversationId.value),
  )
  const isSending = computed(
    () => activeConversationId.value !== null && pendingConversationIds.value.has(activeConversationId.value),
  )

  void restoreConversations()

  async function restoreConversations() {
    try {
      const storedConversations = await listConversations()
      conversations.value = storedConversations.map(({ id, title, character_id, persona_id }) => ({
        id,
        title,
        character_id,
        persona_id,
        messages: [],
      }))
      if (storedConversations.length === 0) {
        activeConversationId.value = null
        localStorage.removeItem('activeConversationId')
        return
      }
      const rememberedId = localStorage.getItem('activeConversationId')
      const activeId = storedConversations.some(({ id }) => id === rememberedId)
        ? rememberedId
        : (storedConversations[0]?.id ?? null)
      if (activeId) await selectConversation(activeId)
    } catch (error: unknown) {
      loadError.value = getErrorMessage(error)
    } finally {
      isLoading.value = false
    }
  }

  async function selectConversation(id: string) {
    const conversation = conversations.value.find((item) => item.id === id)
    if (!conversation) return
    activeConversationId.value = id
    localStorage.setItem('activeConversationId', id)
    if (loadedConversationIds.has(id)) return
    await refreshConversation(id)
  }

  async function refreshConversation(id: string) {
    loadError.value = ''
    try {
      const stored = await getConversation(id)
      const conversation = conversations.value.find((item) => item.id === id)
      if (!conversation) return
      conversation.title = stored.title
      conversation.character_id = stored.character_id
      conversation.persona_id = stored.persona_id
      conversation.messages = stored.messages.map((message) => ({
        id: message.id,
        role: message.role,
        content: message.content,
        time: formatTime(message.created_at),
        isStreaming: message.status === 'pending' || message.status === 'streaming',
        isError: message.status === 'failed',
        isInterrupted: message.status === 'interrupted',
        isSuperseded: message.is_superseded,
      }))
      loadedConversationIds.add(id)
    } catch (error: unknown) {
      loadError.value = getErrorMessage(error)
    }
  }

  async function startNewChat(
    characterId: string,
    personaId: string | null,
    systemPrompt: string,
  ) {
    const id = crypto.randomUUID()
    loadError.value = ''
    try {
      await createConversationRequest(id, characterId, personaId, systemPrompt)
      conversations.value.unshift({
        id,
        title: 'New conversation',
        character_id: characterId,
        persona_id: personaId,
        messages: [],
      })
      loadedConversationIds.add(id)
      activeConversationId.value = id
      localStorage.setItem('activeConversationId', id)
      return true
    } catch (error: unknown) {
      loadError.value = getErrorMessage(error)
      return false
    }
  }

  function sendMessage(content: string) {
    const conversation = activeConversation.value
    const trimmedContent = content.trim()
    if (!conversation) {
      loadError.value = 'No conversation is available. Start a new conversation and try again.'
      return false
    }
    if (!trimmedContent || pendingConversationIds.value.has(conversation.id)) return false

    conversation.messages.push({
      role: 'user',
      content: trimmedContent,
      time: getCurrentTime(),
    })
    if (conversation.title === 'New conversation') {
      conversation.title =
        trimmedContent.length > 60 ? `${trimmedContent.slice(0, 57)}...` : trimmedContent
    }

    const response = reactive<ChatMessage>({
      role: 'assistant',
      content: '',
      time: getCurrentTime(),
      isStreaming: true,
    })
    conversation.messages.push(response)

    void runStream(conversation.id, response, (onToken, onGuidanceSaved) =>
      streamChatReply(trimmedContent, conversation.id, onToken, onGuidanceSaved),
    )
    return true
  }

  function regenerateMessage(messageId: number) {
    const conversation = activeConversation.value
    const response = conversation?.messages.find((item) => item.id === messageId)
    if (
      !conversation ||
      !response ||
      response.role !== 'assistant' ||
      pendingConversationIds.value.has(conversation.id)
    ) {
      return
    }
    response.content = ''
    response.isError = false
    response.isInterrupted = false
    response.isStreaming = true
    void runStream(conversation.id, response, (onToken, onGuidanceSaved) =>
      streamRegeneratedReply(messageId, onToken, onGuidanceSaved),
    )
  }

  async function renameActiveConversation(title: string) {
    const conversation = activeConversation.value
    if (!conversation || pendingConversationIds.value.has(conversation.id)) return
    try {
      await renameConversationRequest(conversation.id, title)
      conversation.title = title
      loadError.value = ''
    } catch (error: unknown) {
      loadError.value = getErrorMessage(error)
    }
  }

  async function removeConversation(id: string) {
    if (pendingConversationIds.value.has(id)) return
    try {
      await deleteConversationRequest(id)
      conversations.value = conversations.value.filter((item) => item.id !== id)
      loadedConversationIds.delete(id)
      if (activeConversationId.value === id) {
        const nextConversation = conversations.value[0]
        if (nextConversation) {
          await selectConversation(nextConversation.id)
        } else {
          activeConversationId.value = null
          localStorage.removeItem('activeConversationId')
        }
      }
      loadError.value = ''
    } catch (error: unknown) {
      loadError.value = getErrorMessage(error)
    }
  }

  async function runStream(
    conversationId: string,
    response: ChatMessage,
    start: (
      onToken: (token: string) => void,
      onGuidanceSaved: () => void,
    ) => Promise<void>,
  ) {
    setPending(conversationId, true)
    loadError.value = ''
    let operationError = ''
    try {
      await start(
        (token) => {
          response.content += token
        },
        () => {
          guidanceSavedCount.value += 1
        },
      )
    } catch (error: unknown) {
      response.isError = true
      operationError = getErrorMessage(error)
      response.content = operationError
    } finally {
      response.isStreaming = false
      await refreshConversation(conversationId)
      const conversation = conversations.value.find((item) => item.id === conversationId)
      if (operationError && !conversation?.messages.at(-1)?.isError) {
        loadError.value = operationError
      }
      setPending(conversationId, false)
    }
  }

  function setPending(conversationId: string, pending: boolean) {
    const nextPending = new Set(pendingConversationIds.value)
    if (pending) nextPending.add(conversationId)
    else nextPending.delete(conversationId)
    pendingConversationIds.value = nextPending
  }

  return {
    activeConversation,
    activeConversationId,
    conversations,
    guidanceSavedCount,
    isLoading,
    isSending,
    loadError,
    deleteConversation: removeConversation,
    regenerateMessage,
    renameConversation: renameActiveConversation,
    selectConversation,
    sendMessage,
    startNewChat,
  }
}

function getCurrentTime() {
  return new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'An unexpected error occurred while loading the chat.'
}

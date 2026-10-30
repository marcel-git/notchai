import type { ChatMessage } from '../types/chat'
import type { ContextMeterData, PromptInspection } from '../types/roleplay'

const CHAT_ENDPOINT = '/api/chat'
const CONVERSATIONS_ENDPOINT = '/api/conversations'

export async function streamChatReply(
  message: string,
  conversationId: string,
  onToken: (token: string) => void,
  onGuidanceSaved: () => void,
  onSummarizationStatus: (isActive: boolean) => void,
) {
  await readEventStream(
    CHAT_ENDPOINT,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    },
    onToken,
    onGuidanceSaved,
    onSummarizationStatus,
  )
}

export async function streamRegeneratedReply(
  messageId: number,
  onToken: (token: string) => void,
  onGuidanceSaved: () => void,
  onSummarizationStatus: (isActive: boolean) => void,
) {
  await readEventStream(
    `/api/messages/${messageId}/regenerate`,
    { method: 'POST' },
    onToken,
    onGuidanceSaved,
    onSummarizationStatus,
  )
}

async function readEventStream(
  endpoint: string,
  init: RequestInit,
  onToken: (token: string) => void,
  onGuidanceSaved: () => void,
  onSummarizationStatus: (isActive: boolean) => void,
) {
  const response = await fetch(endpoint, init)

  if (!response.ok) {
    throw new Error(await readError(response))
  }
  if (!response.body) {
    throw new Error('The chat API returned an empty response stream.')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let receivedDoneEvent = false

  try {
    while (true) {
      const { done, value } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })

      const eventBlocks = buffer.split(/\r?\n\r?\n/)
      buffer = eventBlocks.pop() ?? ''
      for (const block of eventBlocks) {
        receivedDoneEvent =
          processEvent(block, onToken, onGuidanceSaved, onSummarizationStatus) ||
          receivedDoneEvent
      }

      if (done) break
    }

    if (buffer.trim()) {
      receivedDoneEvent =
        processEvent(buffer, onToken, onGuidanceSaved, onSummarizationStatus) ||
        receivedDoneEvent
    }
  } finally {
    reader.releaseLock()
  }

  if (!receivedDoneEvent) {
    throw new Error('The chat API stream ended before the response was complete.')
  }
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const response = await fetch(CONVERSATIONS_ENDPOINT)
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<ConversationSummary[]>
}

export async function getConversation(id: string): Promise<ConversationData> {
  const response = await fetch(`${CONVERSATIONS_ENDPOINT}/${encodeURIComponent(id)}`)
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<ConversationData>
}

export async function createConversation(
  id: string,
  characterId: string,
  personaId: string | null,
  systemPrompt: string,
): Promise<void> {
  const response = await fetch(CONVERSATIONS_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id,
      character_id: characterId,
      persona_id: personaId,
      system_prompt: systemPrompt,
    }),
  })
  if (!response.ok) throw new Error(await readError(response))
}

export async function getPromptPreview(
  characterId: string,
  personaId: string | null,
): Promise<PromptInspection> {
  const response = await fetch(`${CONVERSATIONS_ENDPOINT}/prompt-preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      character_id: characterId,
      persona_id: personaId,
    }),
  })
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<PromptInspection>
}

export async function renameConversation(id: string, title: string): Promise<void> {
  const response = await fetch(`${CONVERSATIONS_ENDPOINT}/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!response.ok) throw new Error(await readError(response))
}

export async function deleteConversation(id: string): Promise<void> {
  const response = await fetch(`${CONVERSATIONS_ENDPOINT}/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw new Error(await readError(response))
}

export async function getPromptInspection(id: string): Promise<PromptInspection> {
  const response = await fetch(
    `${CONVERSATIONS_ENDPOINT}/${encodeURIComponent(id)}/prompt`,
  )
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<PromptInspection>
}

export async function getContextMeter(id: string): Promise<ContextMeterData> {
  const response = await fetch(
    `${CONVERSATIONS_ENDPOINT}/${encodeURIComponent(id)}/context-meter`,
  )
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<ContextMeterData>
}

async function readError(response: Response) {
  try {
    const body: unknown = await response.json()
    if (typeof body === 'object' && body !== null && 'detail' in body) {
      const detail = body.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail)) {
        const messages = detail.flatMap((item: unknown) => {
          if (typeof item !== 'object' || item === null || !('msg' in item)) return []
          if (typeof item.msg !== 'string') return []
          const location =
            'loc' in item && Array.isArray(item.loc)
              ? item.loc.filter(
                  (part: unknown): part is string | number =>
                    typeof part === 'string' || typeof part === 'number',
                )
              : []
          const field = location.filter((part) => part !== 'body').join('.')
          return [field ? `${field}: ${item.msg}` : item.msg]
        })
        if (messages.length) return messages.join(' ')
      }
    }
  } catch {
    // Fall back to the HTTP status when the server did not return JSON.
  }
  return `Chat request failed (${response.status} ${response.statusText}).`
}

type ConversationSummary = {
  id: string
  title: string
  character_id: string | null
  persona_id: string | null
  created_at: string
  updated_at: string
}

type ConversationData = ConversationSummary & {
  messages: Array<{
    id: number
    role: 'user' | 'assistant'
    content: string
    status: 'pending' | 'streaming' | 'completed' | 'interrupted' | 'failed'
    is_superseded: boolean
    created_at: string
  }>
}

function processEvent(
  block: string,
  onToken: (token: string) => void,
  onGuidanceSaved: () => void,
  onSummarizationStatus: (isActive: boolean) => void,
) {
  let event = 'message'
  const dataLines: string[] = []

  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith(':')) continue
    if (line.startsWith('event:')) {
      event = line.slice('event:'.length).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice('data:'.length).trimStart())
    }
  }

  if (dataLines.length === 0) return false

  let data: unknown
  try {
    data = JSON.parse(dataLines.join('\n'))
  } catch {
    throw new Error('The chat API sent an invalid stream event.')
  }

  if (event === 'done') return true
  if (event === 'guidance_saved') {
    onGuidanceSaved()
    return false
  }
  if (event === 'summarizing') {
    onSummarizationStatus(true)
    return false
  }
  if (event === 'summary_finished') {
    onSummarizationStatus(false)
    return false
  }
  if (event === 'error') {
    const message =
      typeof data === 'object' && data !== null && 'error' in data && typeof data.error === 'string'
        ? data.error
        : 'The chat API could not generate a response.'
    throw new Error(message)
  }
  if (event === 'token') {
    if (typeof data !== 'object' || data === null || !('token' in data) || typeof data.token !== 'string') {
      throw new Error('The chat API sent an invalid token event.')
    }
    onToken(data.token)
  }

  return false
}

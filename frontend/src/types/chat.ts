export type MessageRole = 'user' | 'assistant'

export type ChatMessage = {
  id?: number
  role: MessageRole
  content: string
  time: string
  isSuperseded?: boolean
  isStreaming?: boolean
  isSummarizing?: boolean
  isError?: boolean
  isInterrupted?: boolean
}

export type Conversation = {
  id: string
  title: string
  character_id: string | null
  persona_id: string | null
  messages: ChatMessage[]
}

export type Suggestion = {
  icon: string
  title: string
  prompt: string
}

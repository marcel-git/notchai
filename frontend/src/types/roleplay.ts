export type GenerationSettings = {
  model_name: string
  num_predict: number
  temperature: number
  top_p: number
}

export type PromptInspection = {
  conversation_id: string | null
  model_name: string
  num_predict: number
  temperature: number
  top_p: number
  system_prompt: string
}

export type ContextMeterData = {
  conversation_id: string
  model_name: string
  runtime_context_length: number | null
  context_note: string | null
  estimated_tokens_total: number
  sections: Array<{
    label: string
    role: 'system' | 'user' | 'assistant'
    estimated_tokens: number
  }>
}

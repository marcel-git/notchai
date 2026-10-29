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

export type ProfileRecord = {
  [key: string]: string
  id: string
  name: string
  created_at: string
  updated_at: string
}

export type CharacterProfile = ProfileRecord & {
  description: string
  personality: string
  background: string
  custom_instructions: string
}

export type PersonaProfile = ProfileRecord & {
  identity: string
  appearance: string
  background: string
  behavior: string
}

export type CharacterFields = {
  name: string
  description: string
  personality: string
  background: string
  custom_instructions: string
}

export type PersonaFields = {
  name: string
  identity: string
  appearance: string
  background: string
  behavior: string
}

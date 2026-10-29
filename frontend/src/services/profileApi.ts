import type {
  CharacterFields,
  CharacterProfile,
  PersonaFields,
  PersonaProfile,
} from '../types/profiles'

const CHARACTERS_ENDPOINT = '/api/characters'
const PERSONAS_ENDPOINT = '/api/personas'

export function listCharacters(): Promise<CharacterProfile[]> {
  return request<CharacterProfile[]>(CHARACTERS_ENDPOINT)
}

export function createCharacter(fields: CharacterFields): Promise<CharacterProfile> {
  return request<CharacterProfile>(CHARACTERS_ENDPOINT, jsonRequest('POST', fields))
}

export function updateCharacter(
  id: string,
  fields: CharacterFields,
): Promise<CharacterProfile> {
  return request<CharacterProfile>(
    `${CHARACTERS_ENDPOINT}/${encodeURIComponent(id)}`,
    jsonRequest('PUT', fields),
  )
}

export function deleteCharacter(id: string): Promise<void> {
  return remove(`${CHARACTERS_ENDPOINT}/${encodeURIComponent(id)}`)
}

export function listPersonas(): Promise<PersonaProfile[]> {
  return request<PersonaProfile[]>(PERSONAS_ENDPOINT)
}

export function createPersona(fields: PersonaFields): Promise<PersonaProfile> {
  return request<PersonaProfile>(PERSONAS_ENDPOINT, jsonRequest('POST', fields))
}

export function updatePersona(id: string, fields: PersonaFields): Promise<PersonaProfile> {
  return request<PersonaProfile>(
    `${PERSONAS_ENDPOINT}/${encodeURIComponent(id)}`,
    jsonRequest('PUT', fields),
  )
}

export function deletePersona(id: string): Promise<void> {
  return remove(`${PERSONAS_ENDPOINT}/${encodeURIComponent(id)}`)
}

function jsonRequest(method: 'POST' | 'PUT', body: object): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) throw new Error(await readError(response))
  return (await response.json()) as T
}

async function remove(url: string): Promise<void> {
  const response = await fetch(url, { method: 'DELETE' })
  if (!response.ok) throw new Error(await readError(response))
}

async function readError(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (typeof body === 'object' && body !== null && 'detail' in body) {
      const detail = body.detail
      if (typeof detail === 'string') return detail
    }
  } catch {
    // Fall back to the HTTP status when the server did not return JSON.
  }
  return `Profile request failed (${response.status} ${response.statusText}).`
}

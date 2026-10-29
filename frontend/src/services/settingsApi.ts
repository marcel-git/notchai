import type { GenerationSettings } from '../types/roleplay'

const SETTINGS_ENDPOINT = '/api/settings'

export async function getGenerationSettings(): Promise<GenerationSettings> {
  const response = await fetch(SETTINGS_ENDPOINT)
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<GenerationSettings>
}

export async function updateGenerationSettings(
  settings: GenerationSettings,
): Promise<GenerationSettings> {
  const response = await fetch(SETTINGS_ENDPOINT, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  })
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<GenerationSettings>
}

export async function listAvailableModels(): Promise<string[]> {
  const response = await fetch(`${SETTINGS_ENDPOINT}/models`)
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<string[]>
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
  return `Settings request failed (${response.status} ${response.statusText}).`
}

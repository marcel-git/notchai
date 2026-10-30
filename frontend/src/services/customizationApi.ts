import type { GuidanceEntry } from '../types/customization'

const GUIDANCE_ENDPOINT = '/api/customizations/guidance'

export async function listGuidance(): Promise<GuidanceEntry[]> {
  const response = await fetch(GUIDANCE_ENDPOINT)
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<GuidanceEntry[]>
}

export async function addGuidance(text: string): Promise<GuidanceEntry> {
  const response = await fetch(GUIDANCE_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<GuidanceEntry>
}

export async function updateGuidance(
  id: number,
  text: string,
): Promise<GuidanceEntry> {
  const response = await fetch(`${GUIDANCE_ENDPOINT}/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<GuidanceEntry>
}

export async function deleteGuidance(id: number): Promise<void> {
  const response = await fetch(`${GUIDANCE_ENDPOINT}/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
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
  return `Guidance request failed (${response.status} ${response.statusText}).`
}

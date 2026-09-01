import type { Gloss, LessonDetail, LessonSummary, VocabEntry } from './types'

async function call<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
  })
  if (!r.ok) throw new Error((await r.text()) || r.statusText)
  return r.status === 204 ? (undefined as T) : r.json()
}

export const listLessons = () => call<LessonSummary[]>('/api/lessons')

/** Omit `page` to resume where you stopped. */
export const readLesson = (id: number, page?: number) =>
  call<LessonDetail>(`/api/lessons/${id}` + (page === undefined ? '' : `?page=${page}`))

export const deleteLesson = (id: number) =>
  call<void>(`/api/lessons/${id}`, { method: 'DELETE' })

export const importText = (text: string, title: string | null, lang: string) =>
  call<LessonSummary>('/api/lessons', {
    method: 'POST',
    body: JSON.stringify({ text, title: title || null, lang }),
  })

export const setTerm = (t: {
  lang: string
  lemma: string
  pos: string
  status: number
  surface?: string
  note?: string | null
  context?: string | null
  lesson_id?: number
  page?: number
}) => call<{ state: string }>('/api/terms', { method: 'PUT', body: JSON.stringify(t) })

export const undoBulk = (undoId: number) =>
  call<void>(`/api/lessons/undo/${undoId}`, { method: 'POST' })

export const finishPage = (id: number, page: number, markRestKnown: boolean) =>
  call<LessonSummary>(`/api/lessons/${id}/finish`, {
    method: 'POST',
    body: JSON.stringify({ page, mark_rest_known: markRestKnown }),
  })

export const define = (lang: string, lemma: string, pos: string | null) =>
  call<Gloss[]>(
    `/api/dictionary?lang=${lang}&lemma=${encodeURIComponent(lemma)}` +
      (pos ? `&pos=${pos}` : ''),
  )

export const setOverride = (o: {
  lang: string
  surface: string
  from_lemma?: string | null
  to_lemma?: string | null
  to_pos?: string
}) => call<{ lemma: string }>('/api/terms/override', { method: 'PUT', body: JSON.stringify(o) })

export const clearOverride = (lang: string, surface: string) =>
  call<void>(`/api/terms/override?lang=${lang}&surface=${encodeURIComponent(surface)}`, {
    method: 'DELETE',
  })

export const listVocab = (lang: string, status?: string, q?: string) =>
  call<{ total: number; by_status: Record<string, number>; entries: VocabEntry[] }>(
    `/api/vocab?lang=${lang}` +
      (status ? `&status=${status}` : '') +
      (q ? `&q=${encodeURIComponent(q)}` : ''),
  )

import type { LessonDetail, LessonSummary } from './types'

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
}) => call<{ state: string }>('/api/terms', { method: 'PUT', body: JSON.stringify(t) })

export const finishPage = (id: number, page: number, markRestKnown: boolean) =>
  call<LessonSummary>(`/api/lessons/${id}/finish`, {
    method: 'POST',
    body: JSON.stringify({ page, mark_rest_known: markRestKnown }),
  })

import type { Gloss, Health, LessonDetail, LessonSummary, Starter, VocabEntry } from './types'

async function call<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
  })
  if (!r.ok) throw new Error((await r.text()) || r.statusText)
  return r.status === 204 ? (undefined as T) : r.json()
}

/** Version, and which languages this server offers. The language menu is
 *  populated from here rather than from a constant in the bundle: what you can
 *  read is a fact about the server's models, not about the frontend. */
export const health = () => call<Health>('/api/health')

/** The library. With a language, only what you are reading today. */
export const listLessons = (lang?: string) =>
  call<LessonSummary[]>('/api/lessons' + (lang ? `?lang=${lang}` : ''))

/** The texts this language starts with, and whether you have them already. */
export const listStarters = (lang: string) =>
  call<Starter[]>(`/api/lessons/starters?lang=${lang}`)

/** Put the ones you don't have in the library. Pressing twice is a no-op. */
export const addStarters = (lang: string) =>
  call<LessonSummary[]>('/api/lessons/starters', {
    method: 'POST',
    body: JSON.stringify({ lang }),
  })

/** Omit `page` to resume where you stopped. */
export const readLesson = (id: number, page?: number) =>
  call<LessonDetail>(`/api/lessons/${id}` + (page === undefined ? '' : `?page=${page}`))

export const deleteLesson = (id: number) =>
  call<void>(`/api/lessons/${id}`, { method: 'DELETE' })

export const importText = (
  text: string,
  title: string | null,
  lang: string,
  source?: string | null,
) =>
  call<LessonSummary>('/api/lessons', {
    method: 'POST',
    body: JSON.stringify({ text, title: title || null, source: source || null, lang }),
  })

/** Read a page and hand back its text. Importing is a separate press, so bad
 *  extraction can be fixed before it becomes a lesson. */
export const fetchUrl = (url: string) =>
  call<{ text: string; title: string; source: string }>('/api/lessons/fetch', {
    method: 'POST',
    body: JSON.stringify({ url }),
  })

/** Fetch an article and import it. The server does the fetching. */
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

export const listVocab = (lang: string, status?: string, q?: string, sort?: string) =>
  call<{ total: number; by_status: Record<string, number>; entries: VocabEntry[] }>(
    `/api/vocab?lang=${lang}` +
      (status ? `&status=${status}` : '') +
      (q ? `&q=${encodeURIComponent(q)}` : '') +
      (sort ? `&sort=${sort}` : ''),
  )

/** English per sentence for one page, keyed by sent_id. 503 when the optional
 *  translation extra isn't installed. */
export const translation = (id: number, page: number) =>
  call<Record<string, string>>(`/api/lessons/${id}/translation?page=${page}`)

/** A download URL for the lexicon. Given straight to the browser rather than
 *  fetched, so the Content-Disposition header does the saving. */
export const exportUrl = (
  lang: string,
  format: string,
  opts: { status?: string; q?: string; keys?: string[] } = {},
) => {
  const p = new URLSearchParams({ lang, format })
  if (opts.status && opts.status !== 'all') p.set('status', opts.status)
  if (opts.q) p.set('q', opts.q)
  if (opts.keys?.length) p.set('keys', opts.keys.join(','))
  return `/api/vocab/export?${p}`
}

/** Tell the maintainer something is wrong. */
export const sendReport = (text: string, lesson_id?: number, page?: number) =>
  call<{ id: number }>('/api/reports', {
    method: 'POST',
    body: JSON.stringify({ text, lesson_id: lesson_id ?? null, page: page ?? null }),
  })

/** Put a lesson in a collection by name, creating it if new. Empty removes it. */
export const setCollection = (id: number, name: string | null) =>
  call<LessonSummary>(`/api/lessons/${id}/collection`, {
    method: 'PUT',
    body: JSON.stringify({ name }),
  })

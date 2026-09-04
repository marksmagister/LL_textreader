import { useState } from 'react'
import { sendReport } from './api'
import { t } from './i18n'

/** A small box in the corner. Testers will not file a GitHub issue; they will
 *  type one sentence if it takes three seconds. Context (which lesson, which
 *  page) is attached by the caller so nobody has to describe where they were. */
export default function Report({ lessonId, page }: { lessonId?: number; page?: number }) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'failed'>('idle')

  if (!open) {
    return (
      <button className="report-tab" onClick={() => setOpen(true)} title={t('report.tabTitle')}>
        {t('report.tab')}
      </button>
    )
  }

  const send = async () => {
    if (!text.trim()) return
    setState('sending')
    try {
      await sendReport(text.trim(), lessonId, page)
      setState('sent')
      setText('')
      setTimeout(() => (setOpen(false), setState('idle')), 1200)
    } catch {
      setState('failed')
    }
  }

  return (
    <div className="report">
      <textarea
        autoFocus
        value={text}
        maxLength={4000}
        placeholder={t('report.placeholder')}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Escape') setOpen(false)
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send()
        }}
      />
      <p className="bar">
        <button onClick={send} disabled={state === 'sending' || !text.trim()}>
          {state === 'sent'
            ? t('report.sent')
            : state === 'sending'
              ? t('report.sending')
              : t('report.send')}
        </button>
        <button className="ghost" onClick={() => setOpen(false)}>
          {t('report.close')}
        </button>
        {state === 'failed' && <span className="muted">{t('report.failed')}</span>}
      </p>
    </div>
  )
}

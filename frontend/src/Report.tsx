import { useState } from 'react'
import { sendReport } from './api'
import { t } from './i18n'

/** Testers will not file a GitHub issue; they will type one sentence if it takes
 *  three seconds. Context (which lesson, which page) is attached by the caller so
 *  nobody has to describe where they were.
 *
 *  Opened from the account menu and from the palette rather than from a tab of
 *  its own. It used to float in the bottom-right corner, which put it on top of
 *  the word panel — in the margins beside it on a wide screen, and squarely over
 *  its buttons on a narrow one, where "something's wrong" sat on `i ignore`.
 */
export default function Report({
  lessonId,
  page,
  onClose,
}: {
  lessonId?: number
  page?: number
  onClose: () => void
}) {
  const [text, setText] = useState('')
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'failed'>('idle')

  const send = async () => {
    if (!text.trim()) return
    setState('sending')
    try {
      await sendReport(text.trim(), lessonId, page)
      setState('sent')
      setText('')
      setTimeout(onClose, 1200)
    } catch {
      setState('failed')
    }
  }

  return (
    <div className="scrim" onClick={onClose}>
      <div className="report" onClick={(e) => e.stopPropagation()}>
        <textarea
          autoFocus
          value={text}
          maxLength={4000}
          placeholder={t('report.placeholder')}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') onClose()
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
          <button className="ghost" onClick={onClose}>
            {t('report.close')}
          </button>
          {state === 'failed' && <span className="muted">{t('report.failed')}</span>}
        </p>
      </div>
    </div>
  )
}

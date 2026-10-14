import { useState } from 'react'
import styles from './InputPanel.module.css'

const EXAMPLES = [
  { label: "Clothing brand site", text: "Hey bro can you make me a website for my clothing brand, something clean with a shop page and maybe an about us, I want it to look premium. Also add instagram feed somewhere. Budget is around 15k." },
  { label: "Freelance client tracker", text: "Need an app that tracks my freelance clients — who owes me money, project status, invoice dates. Simple UI, maybe mobile friendly too. Nothing too fancy." },
  { label: "Cafe brand kit", text: "I want a logo + full brand kit for my new cafe. Colors should be earthy and warm. Need it for menus, social media, signboard. ASAP basically." },
  { label: "College fest website", text: "bro i need a site for our college fest Invictus, its on nov 15, need registration form, schedule page, speaker bios, and a countdown timer, also make it look fire, budget is 5k" },
]

const TONES = [
  { id: 'professional', label: 'Professional', desc: 'Formal, client-ready language' },
  { id: 'friendly',     label: 'Friendly',     desc: 'Warm but clear boundaries' },
  { id: 'strict',       label: 'Strict',        desc: 'Zero ambiguity, hard edges' },
]

export default function InputPanel({ onGenerate, loading, error }) {
  const [description, setDescription] = useState('')
  const [context, setContext]         = useState('')
  const [showContext, setShowContext]  = useState(false)
  const [tone, setTone]               = useState('professional')
  const [rate, setRate]               = useState('')
  const [showRate, setShowRate]       = useState(false)
  const [focused, setFocused]         = useState(false)

  function handleSubmit(e) {
    e.preventDefault()
    if (!tooShort && !tooLong) {
      const ctx = [
        context,
        tone !== 'professional' ? `Write the scope in a ${tone} tone.` : '',
        rate ? `My hourly rate is ₹${rate}.` : '',
      ].filter(Boolean).join(' ')
      onGenerate(description, ctx)
    }
  }

  const charCount = description.length
  const tooShort  = description.trim().length < 20
  const tooLong   = charCount > 1500

  const charStatus = tooLong
    ? 'danger'
    : charCount > 1400
    ? 'warn'
    : tooShort && charCount > 0
    ? 'danger'
    : 'ok'

  const charLabel = tooShort && charCount > 0
    ? 'Too short — add more detail'
    : `${charCount}/1500`

  return (
    <div className={styles.panel}>
      <div className={styles.hero}>
        <div className={styles.heroLabel}>Freelance scope generator</div>
        <h1 className={styles.headline}>
          Your client said <em>"just a small thing"</em>
        </h1>
        <p className={styles.sub}>
          Paste whatever they sent you — a WhatsApp message, a voice note transcript,
          a rambling email. QuoteShield turns it into a professional scope doc with
          milestones, deliverables, and a "not included" clause. Runs on Mistral 7B,
          entirely on your laptop.
        </p>
        <div className={styles.pillRow}>
          <span className={styles.pill}>🔒 100% offline</span>
          <span className={styles.pill}>⚡ No API key</span>
          <span className={styles.pill}>📋 Copy-ready output</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className={`${styles.form} ${focused ? styles.formFocused : ''}`}>

        {/* Tone selector */}
        <div className={styles.toneRow}>
          <span className={styles.toneLabel}>Scope tone</span>
          <div className={styles.tones}>
            {TONES.map(t => (
              <button
                key={t.id}
                type="button"
                className={`${styles.toneBtn} ${tone === t.id ? styles.toneBtnActive : ''}`}
                onClick={() => setTone(t.id)}
                disabled={loading}
                title={t.desc}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <label className={styles.label} htmlFor="desc">
          Project description
          <span className={styles.hint}>WhatsApp message, email, voice note — anything goes</span>
        </label>
        <textarea
          id="desc"
          className={styles.textarea}
          value={description}
          onChange={e => setDescription(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Hey so I need a website for my salon, something modern with online booking, gallery section, and pricing page. Also maybe add a WhatsApp chat button. Can you do it for 8k?"
          rows={6}
          maxLength={1500}
          disabled={loading}
        />

        <div className={styles.charRow}>
          <span className={styles.charCount} data-status={charStatus}>
            {charLabel}
          </span>
          <div className={styles.rowBtns}>
            <button type="button" className={styles.ghostBtn}
              onClick={() => setShowRate(v => !v)} disabled={loading}>
              {showRate ? '− Rate' : '+ Your rate'}
            </button>
            <button type="button" className={styles.ghostBtn}
              onClick={() => setShowContext(v => !v)} disabled={loading}>
              {showContext ? '− Context' : '+ Context'}
            </button>
          </div>
        </div>

        {showRate && (
          <div className={styles.rateBlock}>
            <label className={styles.label} htmlFor="rate">
              Your hourly rate (₹)
              <span className={styles.hint}>Used to estimate project cost in the output</span>
            </label>
            <div className={styles.rateInput}>
              <span className={styles.ratePre}>₹</span>
              <input
                id="rate"
                type="number"
                className={styles.input}
                value={rate}
                onChange={e => setRate(e.target.value)}
                placeholder="2000"
                min="0"
                disabled={loading}
              />
              <span className={styles.ratePost}>/hr</span>
              {rate && description && (
                <span className={styles.rateCalc}>
                  ≈ ₹{(parseInt(rate) * 40).toLocaleString('en-IN')}–₹{(parseInt(rate) * 80).toLocaleString('en-IN')} estimated range
                </span>
              )}
            </div>
          </div>
        )}

        {showContext && (
          <div className={styles.contextBlock}>
            <label className={styles.label} htmlFor="ctx">
              Your constraints
              <span className={styles.hint}>Stack preferences, things you never do, timeline limits</span>
            </label>
            <textarea
              id="ctx"
              className={styles.textarea}
              value={context}
              onChange={e => setContext(e.target.value)}
              placeholder="I only work with React. I don't do SEO or copywriting. Max 4 weeks."
              rows={3}
              disabled={loading}
            />
          </div>
        )}

        {error && (
          <div className={styles.error}>
            <span>⚠ {error}</span>
          </div>
        )}

        <button type="submit" className={styles.submit} disabled={loading || tooShort || tooLong}>
          {loading ? (
            <span className={styles.spinner}>
              <span className={styles.dot} />
              <span className={styles.dot} style={{ animationDelay: '0.15s' }} />
              <span className={styles.dot} style={{ animationDelay: '0.3s' }} />
              Generating scope…
            </span>
          ) : (
            <>Generate scope doc <span className={styles.arrow}>→</span></>
          )}
        </button>
      </form>

      <div className={styles.examples}>
        <p className={styles.exLabel}>Quick examples</p>
        <div className={styles.exGrid}>
          {EXAMPLES.map((ex, i) => (
            <button key={i} className={styles.exBtn}
              onClick={() => setDescription(ex.text)} disabled={loading}>
              <span className={styles.exTitle}>{ex.label}</span>
              <span className={styles.exPreview}>{ex.text.slice(0, 55)}…</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

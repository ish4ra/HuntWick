import { useEffect, useRef, useState, type FormEvent } from 'react'
import {
  ArrowRight,
  AtSign,
  Check,
  ChevronDown,
  CircleDot,
  Globe2,
  Github,
  Gitlab,
  ShieldCheck,
  Layers3,
  LocateFixed,
  Radar,
  Search,
  SlidersHorizontal,
  Square,
  X,
  Zap,
} from 'lucide-react'
import { validUsername, type Mode } from '../model'
import { Busy, isActive, webPrivacy, type Workspace } from './common'
import Results from './Results'

function ScopeRadar({ active }: { active: boolean }) {
  return (
    <div className={'scope-radar' + (active ? ' scanning' : '')} aria-hidden="true">
      <div className="radar-grid" />
      <div className="radar-axis-x" />
      <div className="radar-axis-y" />
      <div className="radar-disc">
        <div className="sweep" />
        <i />
        <i />
        <i />
        <i />
        <b />
      </div>
      <span className="radar-label radar-n">N</span>
      <span className="radar-label radar-e">E</span>
      <i className="corner tl" />
      <i className="corner tr" />
      <i className="corner bl" />
      <i className="corner br" />
    </div>
  )
}
export function NumberSetting({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  onChange: (n: number) => void
}) {
  const [draft, setDraft] = useState(String(value))
  useEffect(() => setDraft(String(value)), [value])
  function commit() {
    const next =
      draft.trim() && Number.isFinite(Number(draft))
        ? Math.max(min, Math.min(max, Math.trunc(Number(draft))))
        : value
    setDraft(String(next))
    onChange(next)
  }
  return (
    <label className="number-setting">
      {label}
      <input
        type="number"
        min={min}
        max={max}
        step={1}
        value={draft}
        onChange={(e) => {
          const s = e.target.value
          setDraft(s)
          const n = Number(s)
          if (s && Number.isInteger(n) && n >= min && n <= max) onChange(n)
        }}
        onBlur={commit}
      />
    </label>
  )
}
export default function SearchPage({ ws, focusToken }: { ws: Workspace; focusToken: number }) {
  const [username, setUsername] = useState(ws.run?.username ?? '')
  const [mode, setMode] = useState<Mode>(ws.run?.mode ?? ws.settings.defaultMode)
  const [advanced, setAdvanced] = useState(false)
  const [validation, setValidation] = useState('')
  const input = useRef<HTMLInputElement>(null)
  const active = isActive(ws.run)
  const quick =
    ws.catalog?.sites.filter((s) => s.quick && !ws.settings.disabledSites.includes(s.name)).length ?? 0
  const full = ws.catalog?.sites.filter((s) => !ws.settings.disabledSites.includes(s.name)).length ?? 0
  const count = ws.hosted || mode === 'full' ? full : quick
  function togglePlatform(platform: string) {
    const disabled = ws.settings.disabledSites
    ws.updateSettings({
      disabledSites: disabled.includes(platform)
        ? disabled.filter((name) => name !== platform)
        : [...disabled, platform],
    })
  }
  useEffect(() => {
    if (focusToken) input.current?.focus()
  }, [focusToken])
  async function submit(event: FormEvent) {
    event.preventDefault()
    const name = username.trim()
    if (!validUsername(name)) {
      setValidation('Enter a username of 1–64 letters, numbers, periods, hyphens or underscores.')
      input.current?.focus()
      return
    }
    setValidation('')
    await ws.start(name, ws.hosted ? 'full' : mode)
  }
  return (
    <>
      <div className="page-intro search-intro">
        <div className="eyebrow">
          <span /> {ws.hosted ? 'WEB EDITION · PRIVATE PREVIEW' : 'PROFILE DISCOVERY'}
        </div>
        <h1>Username search</h1>
        <p>
          {ws.hosted
            ? 'Check a username for public profiles on selected development platforms.'
            : 'Find public profiles across platforms with a single username.'}
        </p>
      </div>
      <section className="search-panel" aria-labelledby="target-heading">
        <div className="console-heading">
          <div className="console-title">
            <LocateFixed size={16} />
            <h2 id="target-heading">Search console</h2>
          </div>
          <span className={'standby' + (active ? ' live' : '')}>
            <i />
            {active ? 'Running' : ws.ready ? 'Ready' : 'Standby'}
          </span>
        </div>
        <form onSubmit={submit} noValidate>
          <div className="console-body">
            <div className="fields">
              <label htmlFor="username">Target username</label>
              <div className="search-line">
                <div className={'user-input' + (validation ? ' invalid' : '')}>
                  <AtSign size={17} />
                  <input
                    ref={input}
                    id="username"
                    value={username}
                    disabled={active}
                    spellCheck={false}
                    autoCapitalize="none"
                    autoComplete="off"
                    placeholder="Enter a username"
                    aria-invalid={!!validation}
                    aria-describedby={validation ? 'validation' : undefined}
                    onChange={(e) => {
                      setUsername(e.target.value)
                      setValidation('')
                    }}
                  />
                </div>
                {active ? (
                  <button
                    className="primary cancel"
                    type="button"
                    disabled={ws.run?.phase === 'cancelling'}
                    onClick={() => void ws.cancel()}
                  >
                    <Square size={14} />
                    Cancel
                  </button>
                ) : (
                  <button className="primary" type="submit" disabled={!ws.ready || count === 0}>
                    <Search size={16} />
                    Search
                    <ArrowRight size={15} className="go-arrow" />
                  </button>
                )}
              </div>
              {validation && (
                <p className="issue" id="validation" role="alert">
                  {validation}
                </p>
              )}
              {ws.hosted ? (
                <fieldset className="web-platforms" disabled={active}>
                  <legend>Platforms to check</legend>
                  {ws.catalog?.sites.map((site) => {
                    const enabled = !ws.settings.disabledSites.includes(site.name)
                    const Icon = site.name === 'GitHub' ? Github : site.name === 'GitLab' ? Gitlab : Globe2
                    return (
                      <label key={site.name} className={'platform-choice' + (enabled ? ' enabled' : '')}>
                        <Icon size={16} />
                        <span>{site.name}</span>
                        <input type="checkbox" checked={enabled} onChange={() => togglePlatform(site.name)} />
                      </label>
                    )
                  })}
                  {!ws.catalog && <span className="scope-caption">Awaiting the hosted catalog…</span>}
                </fieldset>
              ) : (
                <>
                  {' '}
                  <div className="mode-heading" id="mode-label">
                    Search mode
                  </div>
                  <div className="modes" role="group" aria-labelledby="mode-label">
                    {(
                      [
                        { key: 'quick', name: 'Quick search', count: quick, Icon: Zap },
                        { key: 'full', name: 'Full search', count: full, Icon: Layers3 },
                      ] as const
                    ).map(({ key, name, count: n, Icon }) => (
                      <button
                        key={key}
                        type="button"
                        className={'mode' + (mode === key ? ' active' : '')}
                        disabled={active}
                        aria-pressed={mode === key}
                        onClick={() => setMode(key)}
                      >
                        <Icon size={17} />
                        <span>
                          <strong>{name}</strong>
                          <small>{ws.catalog ? n : '—'} platforms</small>
                        </span>
                        <span className="radio-mark">
                          {mode === key && <Check size={9} strokeWidth={4} />}
                        </span>
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
            <ScopeRadar active={active} />
          </div>
          <div className="console-foot">
            <button
              type="button"
              className="advanced"
              aria-expanded={advanced}
              onClick={() => setAdvanced(!advanced)}
            >
              <SlidersHorizontal size={14} />
              Advanced options
              <ChevronDown className={advanced ? 'rotated' : ''} size={13} />
            </button>
            {(ws.run || username) && !active ? (
              <button
                type="button"
                className="text-action"
                onClick={() => {
                  ws.clearRun()
                  setUsername('')
                  setValidation('')
                  input.current?.focus()
                }}
              >
                <X size={13} /> Clear search
              </button>
            ) : (
              <span className="scope-caption">
                <Globe2 size={13} />
                {ws.catalog ? ws.catalog.sites.length + ' platforms in catalog' : 'Platform catalog'}
              </span>
            )}
          </div>
          {advanced && (
            <fieldset disabled={active} className="advanced-panel">
              <legend className="sr-only">Search limits</legend>
              <NumberSetting
                label="Timeout (seconds)"
                value={ws.settings.timeout}
                min={1}
                max={ws.maxTimeout}
                onChange={(timeout) => ws.updateSettings({ timeout })}
              />
              <NumberSetting
                label="Concurrent checks"
                value={ws.settings.concurrency}
                min={1}
                max={ws.maxConcurrency}
                onChange={(concurrency) => ws.updateSettings({ concurrency })}
              />
            </fieldset>
          )}
        </form>
      </section>
      {ws.hosted && (
        <aside className="web-notice" aria-label="Authorized use and privacy">
          <ShieldCheck size={18} />
          <div>
            <strong>For authorized testing</strong>
            <p>Check only usernames you own or have permission to investigate. {webPrivacy}</p>
          </div>
        </aside>
      )}
      {!ws.catalog && !ws.error && (
        <div className="catalog-notice">
          <Busy /> Loading platform catalog…
        </div>
      )}
      {ws.catalog && count === 0 && (
        <div className="catalog-notice">
          <CircleDot size={15} />
          {ws.hosted
            ? 'Select at least one platform above to search.'
            : 'Enable platforms for this mode in the Platforms view.'}
        </div>
      )}
      <Results key={ws.run?.id ?? 'empty'} ws={ws} />
      <p className="note">
        <Radar size={14} />
        Platform responses are leads. A shared username alone does not establish identity.
      </p>
    </>
  )
}

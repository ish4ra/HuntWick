import { useMemo, useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  ChevronRight,
  Clock3,
  Database,
  History,
  Layers3,
  Search,
  ShieldCheck,
  Trash2,
  Zap,
} from 'lucide-react'
import { PlatformMark, dateTime, Empty, isActive, phases, Toggle, type Page, type Workspace } from './common'

export function Intro({ label, title, description }: { label: string; title: string; description: string }) {
  return (
    <div className="page-intro">
      <div className="eyebrow">
        <span />
        {label}
      </div>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  )
}
export function HistoryPage({ ws, navigate }: { ws: Workspace; navigate: (page: Page) => void }) {
  const [confirm, setConfirm] = useState(false)
  const [query, setQuery] = useState('')
  const historyLocation = ws.hosted ? 'in this browser' : 'on this device'
  const filtered = ws.history.filter((r) => r.username.toLowerCase().includes(query.trim().toLowerCase()))
  return (
    <>
      <Intro
        label="LOCAL RECORDS"
        title="Search history"
        description={`Revisit searches saved ${historyLocation}.`}
      />
      <div className="pref-banner">
        <ShieldCheck size={21} />
        <div>
          <strong>Local search history</strong>
          <small>
            {ws.settings.saveHistory
              ? `New searches are saved ${historyLocation}.`
              : `Enable history to save future searches ${historyLocation}.`}
          </small>
        </div>
        <Toggle
          checked={ws.settings.saveHistory}
          label="Save search history"
          onChange={() => ws.updateSettings({ saveHistory: !ws.settings.saveHistory })}
        />
      </div>
      <div className="section-heading">
        <div className="heading-with-icon">
          <History size={20} />
          <h2>Saved searches</h2>
          <span className="count-tag">{ws.history.length}</span>
        </div>
        {!!ws.history.length && (
          <button className="quiet small" onClick={() => setConfirm(!confirm)}>
            <Trash2 size={14} />
            Clear history
          </button>
        )}
      </div>
      {confirm && (
        <div className="confirmation" role="alert">
          <span>Delete all saved searches from this {ws.hosted ? 'browser' : 'device'}?</span>
          <button className="quiet small" onClick={() => setConfirm(false)}>
            Keep history
          </button>
          <button
            className="danger small"
            onClick={() => {
              ws.clearHistory()
              setConfirm(false)
            }}
          >
            Delete all
          </button>
        </div>
      )}
      <section className="result-panel">
        {!!ws.history.length && (
          <div className="library-toolbar">
            <label className="input-icon">
              <Search size={15} />
              <input
                aria-label="Filter history by username"
                placeholder="Filter by username"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </label>
          </div>
        )}
        {!filtered.length ? (
          <Empty
            icon={<Clock3 size={25} />}
            title={ws.history.length ? 'No matching searches' : 'No saved searches'}
          >
            {ws.history.length
              ? 'Try another username.'
              : ws.settings.saveHistory
                ? 'Completed searches will appear here.'
                : 'History is turned off.'}
          </Empty>
        ) : (
          <div className="history-list">
            {filtered.map((run) => (
              <div className="history-row" key={run.id}>
                <span className="platform-icon">
                  <History size={17} />
                </span>
                <div className="history-name">
                  <strong>@{run.username}</strong>
                  <small>{dateTime(run.startedAt)}</small>
                  <span>{run.results.filter(r=>r.status==='found'||r.status==='possible').slice(0,4).map(r=><span key={r.platform} title={r.platform}><PlatformMark name={r.platform}/></span>)}</span>
                </div>
                <span className="history-phase">{phases[run.phase]}</span>
                <span>{run.results.filter(r => r.status === 'found').length} verified · {run.results.filter(r => r.status === 'possible').length} possible</span>
                <button
                  className="quiet small"
                  disabled={isActive(ws.run)}
                  onClick={() => {
                    ws.loadHistory(run.id)
                    navigate('Search')
                  }}
                  aria-label={'View search for ' + run.username}
                >
                  View <ChevronRight size={13} />
                </button>
                <button
                  className="icon-button"
                  aria-label={'Delete saved search for ' + run.username}
                  title="Delete saved search"
                  onClick={() => ws.deleteHistory(run.id)}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  )
}
export function PlatformsPage({ ws }: { ws: Workspace }) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [scope, setScope] = useState('all')
  const [current, setCurrent] = useState(0)
  const sites = ws.catalog?.sites ?? []
  const categories = [...new Set(sites.map((s) => s.category))].sort()
  const disabled = useMemo(() => new Set(ws.settings.disabledSites), [ws.settings.disabledSites])
  const unavailable = ws.catalog?.unavailable ?? []
  const directory = [
    ...sites.map(site => ({ ...site, reason: '' })),
    ...unavailable.map(entry => ({ ...entry, category: '', quick: false })),
  ]
  const filtered = directory
    .filter(
      (s) =>
        s.name.toLowerCase().includes(query.trim().toLowerCase()) &&
        (!category || s.category === category) &&
        (scope === 'all' ||
          (scope === 'quick' && s.quick) ||
          (scope === 'enabled' && !s.reason && !disabled.has(s.name)) ||
          (scope === 'unavailable' && !!s.reason) ||
          (scope === 'disabled' && !s.reason && disabled.has(s.name))),
    )
    .sort((a, b) => a.name.localeCompare(b.name))
  const pages = Math.max(1, Math.ceil(filtered.length / 20))
  const page = Math.min(current, pages - 1)
  const enabled = sites.filter((s) => !disabled.has(s.name)).length
  function toggle(name: string) {
    const next = new Set(ws.settings.disabledSites)
    if (next.has(name)) next.delete(name)
    else next.add(name)
    ws.updateSettings({ disabledSites: [...next] })
  }
  return (
    <>
      <Intro
        label="SOURCE DIRECTORY"
        title="Platforms"
        description={
          ws.hosted
            ? 'Choose which approved platforms to include in web searches.'
            : 'Explore the platform catalog and choose which sites to include in searches.'
        }
      />
      <div className="library-stats">
        {[
          { label: 'Available platforms', value: sites.length, Icon: Database },
          { label: 'Enabled platforms', value: enabled, Icon: Layers3 },
          {
            label: ws.hosted ? 'Disabled platforms' : 'Quick search platforms',
            value: ws.hosted
              ? sites.length - enabled
              : sites.filter((s) => s.quick && !disabled.has(s.name)).length,
            Icon: Zap,
          },
        ].map(({ label, value, Icon }) => (
          <div key={label}>
            <Icon size={18} />
            <strong>{ws.catalog ? value : '—'}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <div className="section-heading">
        <div className="heading-with-icon">
          <Layers3 size={20} />
          <h2>Platform directory</h2>
        </div>
      </div>
      <section className="result-panel">
        <div className="library-toolbar">
          <label className="input-icon">
            <Search size={15} />
            <input
              aria-label="Search platform names"
              value={query}
              placeholder="Search platforms"
              onChange={(e) => {
                setQuery(e.target.value)
                setCurrent(0)
              }}
            />
          </label>
          <select
            aria-label="Platform category"
            value={category}
            onChange={(e) => {
              setCategory(e.target.value)
              setCurrent(0)
            }}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <select
            aria-label="Platform scope"
            value={scope}
            onChange={(e) => {
              setScope(e.target.value)
              setCurrent(0)
            }}
          >
            <option value="all">All platforms</option>
            <option value="enabled">Enabled</option>
            <option value="disabled">Disabled</option>
            {!ws.hosted && <option value="quick">Quick search</option>}
            {!ws.hosted && <option value="unavailable">Unavailable ({unavailable.length})</option>}
          </select>
        </div>
        {!filtered.length ? (
          <Empty
            icon={<Search size={23} />}
            title={ws.catalog ? 'No platforms found' : 'Catalog unavailable'}
          >
            {ws.catalog
              ? 'Try another filter or platform name.'
              : ws.hosted
                ? 'The hosted platform catalog could not be loaded.'
                : 'The platform catalog loads from the local engine.'}
          </Empty>
        ) : (
          <>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Platform</th>
                    <th>Category</th>
                    {!ws.hosted && <th>Search mode</th>}
                    <th>Enabled</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.slice(page * 20, (page + 1) * 20).map((s) => (
                    <tr key={s.name}>
                      <td className="strong"><PlatformMark name={s.name}/> {s.name}</td>
                      {s.reason ? <td colSpan={3}><strong>Unavailable</strong><small className="exclusion-reason">{s.reason}</small></td> : <>
                      <td>{s.category}</td>
                      {!ws.hosted && (
                        <td>
                          {s.quick ? (
                            <span className="quick-label">
                              <Zap size={12} /> Quick &amp; full
                            </span>
                          ) : (
                            'Full'
                          )}
                        </td>
                      )}
                      <td>
                        <Toggle
                          checked={!disabled.has(s.name)}
                          label={'Enable ' + s.name}
                          onChange={() => toggle(s.name)}
                        />
                      </td>
                      </>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination">
              <span>
                {page * 20 + 1}–{Math.min((page + 1) * 20, filtered.length)} of {filtered.length} platforms
              </span>
              <div>
                <button
                  className="icon-button"
                  aria-label="Previous page"
                  disabled={!page}
                  onClick={() => setCurrent(page - 1)}
                >
                  <ArrowLeft size={15} />
                </button>
                <button
                  className="icon-button"
                  aria-label="Next page"
                  disabled={page + 1 >= pages}
                  onClick={() => setCurrent(page + 1)}
                >
                  <ArrowRight size={15} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </>
  )
}

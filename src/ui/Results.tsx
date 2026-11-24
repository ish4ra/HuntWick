import { useMemo, useState } from 'react'
import {
  ArrowDownAZ,
  ChevronDown,
  CircleCheck,
  Download,
  ExternalLink,
  LayoutGrid,
  List,
  ListFilter,
  Radio,
  Search,
  SlidersHorizontal,
} from 'lucide-react'
import {
  Busy,
  CopyLink,
  Empty,
  PlatformMark,
  isActive,
  phases,
  statuses,
  useElapsed,
  type Workspace,
} from './common'
import { countStatuses, matchLinks, visibleIn, type Result, type ResultView, type Status } from '../model'

function ProfileLink({ row, ws }: { row: Result; ws: Workspace }) {
  if (!row.url) return <span className="muted">Unavailable</span>
  return (
    <span className="profile-link">
      <button title={row.url} onClick={() => void ws.openUrl(row.url)}>
        <span>{row.url}</span>
        <ExternalLink size={12} />
      </button>
      <CopyLink url={row.url} />
    </span>
  )
}
function Evidence({ row }: { row: Result }) {
  return <>
    {row.message && <small className="row-detail">{row.message}</small>}
    {row.reason && row.reason !== row.message && <small className="row-detail">{row.reason}</small>}
  </>
}
function StatusPill({ status }: { status: Status }) {
  return (
    <span className={'result-status status-' + status}>
      <i />
      {statuses[status]}
    </span>
  )
}
export default function Results({ ws }: { ws: Workspace }) {
  const { run } = ws
  const [layout, setLayout] = useState<'table' | 'cards'>('table')
  const [view, setView] = useState<ResultView>('balanced')
  const [filter, setFilter] = useState<Status | 'all'>('all')
  const [category, setCategory] = useState('')
  const [query, setQuery] = useState('')
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [ascending, setAscending] = useState(true)
  const [exportsOpen, setExportsOpen] = useState(false)
  const elapsed = useElapsed(run)
  const active = isActive(run)
  const rows = run?.results ?? []
  const counts = countStatuses(rows)
  const matches = counts.found + counts.possible
  const views: { key: ResultView; label: string; count: number; hint: string }[] = [
    { key: 'balanced', label: 'Balanced', count: matches, hint: 'Verified and possible matches' },
    { key: 'strict', label: 'Strict', count: counts.found, hint: 'Verified matches only' },
    { key: 'diagnostics', label: 'Diagnostics', count: rows.length - matches, hint: 'Non-match statuses and check failures' },
    { key: 'all', label: 'All results', count: rows.length, hint: 'Every platform result' },
  ]
  const checked = run?.checked ?? 0
  const filtered = useMemo(
    () =>
      (run?.results ?? [])
        .filter(
          (r) =>
            visibleIn(r.status, view) && (filter === 'all' || r.status === filter) &&
            (!category || r.category === category) &&
            (r.platform + ' ' + r.url).toLowerCase().includes(query.trim().toLowerCase()),
        )
        .sort((a, b) => a.platform.localeCompare(b.platform) * (ascending ? 1 : -1)),
    [run?.results, view, filter, category, query, ascending],
  )
  const categories = [...new Set(rows.map((row) => row.category))].sort()
  return (
    <section className="result-area" aria-label="Search results">
      <div className="section-heading">
        <div className="heading-with-icon">
          <ListFilter size={21} />
          <h2>Search results</h2>
          {run && <span className="count-tag">{rows.length}</span>}
        </div>
        <div className="actions">
          {run && (
            <span className="run-state">
              {active ? <Busy /> : <CircleCheck size={14} />} {phases[run.phase]}
            </span>
          )}
          {run && <>
            <CopyLink url={matchLinks(rows, 'found')} action="Copy verified links" />
            <CopyLink url={matchLinks(rows, 'possible')} action="Copy possible links" />
          </>}
          <div className="menu-anchor">
            <button
              className="quiet small"
              disabled={!rows.length || active}
              aria-expanded={exportsOpen}
              onClick={() => setExportsOpen(!exportsOpen)}
            >
              <Download size={14} /> Export <ChevronDown size={12} />
            </button>
            {exportsOpen && (
              <div
                className="popover"
                onKeyDown={(e) => {
                  if (e.key === 'Escape') setExportsOpen(false)
                }}
              >
                {(['csv', 'json', 'html', 'diagnostics'] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => {
                      setExportsOpen(false)
                      void ws.exportRun(f)
                    }}
                  >
                    {f === 'diagnostics' ? 'Export diagnostics (no handle or URLs)' : 'Export '+f.toUpperCase()}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="result-panel">
        {run && (
          <div className="run-summary">
            <div className="summary-title">
              <span>
                Results for <strong>@{run.username}</strong>
              </span>
              <span className="mono">{elapsed} elapsed</span>
            </div>
            <div className="progress-caption">
              <span>{checked} checked of {run.sites.length} selected</span>
              <span>{run.sites.length - rows.length} pending</span>
            </div>
            <progress aria-label="Selected platforms with an outcome" max={Math.max(1, run.sites.length)} value={rows.length} />
            <dl className="stats">
              {(Object.keys(statuses) as Status[]).map(status => (
                <div key={status}>
                  <dt>{statuses[status]}</dt>
                  <dd>{counts[status]}</dd>
                </div>
              ))}
            </dl>
            {run.error && (
              <p className="issue" role="alert">
                {run.error}
              </p>
            )}
          </div>
        )}
        <div className="results-toolbar">
          <div className="filter-tabs" role="group" aria-label="Result view">
            {views.map(option => (
              <button key={option.key} className={view === option.key ? 'chosen' : ''}
                title={option.hint} aria-pressed={view === option.key}
                onClick={() => { setView(option.key); setFilter('all') }}>
                {option.label} <b>{option.count}</b>
              </button>
            ))}
          </div>
          <div className="actions toolbar-actions">
            <button
              className={'filter-button' + (filtersOpen ? ' selected' : '')}
              aria-expanded={filtersOpen}
              onClick={() => setFiltersOpen(!filtersOpen)}
            >
              <SlidersHorizontal size={14} /> Filters
            </button>
            <i className="separator" />
            <div className="view-switch">
              <button
                className={layout === 'table' ? 'selected' : ''}
                onClick={() => setLayout('table')}
                aria-label="Table view"
                title="Table view"
                aria-pressed={layout === 'table'}
              >
                <List size={15} />
              </button>
              <button
                className={layout === 'cards' ? 'selected' : ''}
                onClick={() => setLayout('cards')}
                aria-label="Card view"
                title="Card view"
                aria-pressed={layout === 'cards'}
              >
                <LayoutGrid size={14} />
              </button>
            </div>
          </div>
        </div>
        {run && <p className="view-description">{views.find(option => option.key === view)?.hint}</p>}
        {filtersOpen && (
          <div className="filters">
            <label>
              Platform or URL
              <div className="input-icon">
                <Search size={15} />
                <input
                  placeholder="Filter results"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
            </label>
            <label>
              Status
              <select
                aria-label="Status"
                value={filter}
                onChange={(e) => { setView('all'); setFilter(e.target.value as typeof filter) }}
              >
                <option value="all">All statuses</option>
                {Object.entries(statuses).map(([k, v]) => (
                  <option value={k} key={k}>
                    {v}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Category
              <select aria-label="Category" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">All categories</option>
                {categories.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </label>
            <button className="quiet small" onClick={() => setAscending(!ascending)}>
              <ArrowDownAZ size={14} />
              {ascending ? 'A–Z' : 'Z–A'}
            </button>
          </div>
        )}
        {!run ? (
          <Empty icon={<Radio size={27} />} title="Awaiting your first search">
            Enter a username above to discover public profiles.
          </Empty>
        ) : filtered.length === 0 ? (
          <Empty
            icon={active ? <Busy /> : <Search size={24} />}
            title={active ? 'Checking public profiles' : 'No results in this view'}
          >
            {active
              ? 'Results appear here as platform checks finish.'
              : 'Try another status or adjust your filters.'}
          </Empty>
        ) : layout === 'cards' ? (
          <div className="profile-cards">
            {filtered.map((row) => (
              <article key={row.platform} className="profile-card">
                <div className="card-title">
                  <PlatformMark name={row.platform} />
                  <div className="profile-id">
                    <strong>{row.platform}</strong>
                    <small>@{run.username}</small>
                  </div>
                </div>
                <div className="card-meta">
                  <StatusPill status={row.status} />
                  <span>{row.category}</span>
                </div>
                <ProfileLink row={row} ws={ws} />
                <Evidence row={row} />
              </article>
            ))}
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>
                    <button className="sort-header" onClick={() => setAscending(!ascending)}>
                      Platform <ArrowDownAZ size={13} />
                    </button>
                  </th>
                  <th>Status</th>
                  <th>Category</th>
                  <th>Profile URL</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr key={row.platform}>
                    <td>
                      <div className="platform-cell">
                        <PlatformMark name={row.platform} />
                        <div className="profile-id">
                          <strong>{row.platform}</strong>
                          <small>@{run.username}</small>
                        </div>
                      </div>
                    </td>
                    <td title={row.message}>
                      <StatusPill status={row.status} />
                      <Evidence row={row} />
                    </td>
                    <td>{row.category}</td>
                    <td>
                      <ProfileLink row={row} ws={ws} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}

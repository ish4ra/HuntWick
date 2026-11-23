export type Mode = 'quick' | 'full'
export type Status = 'found' | 'not_found' | 'inconclusive' | 'timed_out' | 'blocked' | 'cancelled' | 'error'
export type Phase = 'running' | 'cancelling' | 'complete' | 'cancelled' | 'error'
export type ExportFormat = 'csv' | 'json' | 'html'

export interface Site {
  name: string
  url: string
  category: string
  quick: boolean
}
export interface Catalog {
  version: string
  databaseVersion: string
  updatedAt: string
  sites: Site[]
}
export interface Result {
  platform: string
  url: string
  category: string
  status: Status
  message: string
}
export interface Run {
  id: string
  username: string
  startedAt: string
  finishedAt: string | null
  mode: Mode
  sites: string[]
  results: Result[]
  checked: number
  phase: Phase
  error: string | null
}
export interface Settings {
  rememberPreferences: boolean
  timeout: number
  concurrency: number
  saveHistory: boolean
  defaultMode: Mode
  theme: 'dark' | 'light' | 'system'
  density: 'compact' | 'comfortable'
  disabledSites: string[]
}

const statuses: ReadonlySet<string> = new Set<Status>(['found', 'not_found', 'inconclusive', 'timed_out', 'blocked', 'cancelled', 'error'])
export const historyLimit = 20

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
function shortString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0 && value.length <= 256
}
export function validUsername(value: unknown): value is string {
  return typeof value === 'string' && value.length >= 1 && value.length <= 64 &&
    !/[^A-Za-z0-9._-]/.test(value) && value !== '.' && value !== '..'
}
function validStatus(value: unknown): value is Status {
  return typeof value === 'string' && statuses.has(value)
}

/** Only open ordinary public web origins. Recheck this at the native boundary too. */
export function safeUrl(value: unknown): string {
  if (typeof value !== 'string' || value.length > 4096 || !/^https:\/\//i.test(value)) return ''
  if (Array.from(value).some(c => c.charCodeAt(0) <= 32 || c.charCodeAt(0) === 127) || value.includes('\\')) return ''
  try {
    const url = new URL(value)
    const host = url.hostname.toLowerCase().replace(/\.$/, '')
    if (url.username || url.password || url.port || !host.includes('.') || !/^[a-z\d.-]+$/.test(host) ||
      /^[0-9.]+$/.test(host) || /\.(localhost|local|internal|lan|home|onion)$/.test(host)) return ''
    return url.href
  } catch {
    return ''
  }
}

export function parseCatalog(value: unknown): Catalog {
  if (!record(value) || !shortString(value.version) || !shortString(value.databaseVersion) ||
    !shortString(value.updatedAt) || !Array.isArray(value.sites) || !value.sites.length) {
    throw new Error('The engine returned an invalid platform catalog.')
  }
  const seen = new Set<string>()
  const sites = value.sites.map((s: unknown) => {
    if (!record(s) || !shortString(s.name) || !shortString(s.category) || typeof s.quick !== 'boolean' ||
      !safeUrl(s.url) || seen.has(s.name)) throw new Error('The engine returned an invalid platform entry.')
    seen.add(s.name)
    return { name: s.name, category: s.category, quick: s.quick, url: safeUrl(s.url) }
  })
  return { version: value.version, databaseVersion: value.databaseVersion, updatedAt: value.updatedAt, sites }
}

export function selectSites(catalog: Catalog, mode: Mode, disabled: string[], selected?: string[]): Site[] {
  const excluded = new Set(disabled)
  const explicit = selected ? new Set(selected) : null
  return catalog.sites.filter(s => !excluded.has(s.name) && (explicit ? explicit.has(s.name) : mode === 'full' || s.quick))
}

export function createRun(id: string, username: string, mode: Mode, sites: Site[], now: string): Run {
  return { id, username, startedAt: now, finishedAt: null, mode, sites: sites.map(s => s.name), results: [], checked: 0, phase: 'running', error: null }
}

export function activeRun(run: Run | null): boolean {
  return run?.phase === 'running' || run?.phase === 'cancelling'
}

function finishRun(run: Run, catalog: Catalog, now: string, phase: 'cancelled' | 'complete' | 'error', message: string): Run {
  const results = [...run.results]
  const received = new Set(results.map(r => r.platform))
  for (const site of catalog.sites) {
    if (run.sites.includes(site.name) && !received.has(site.name)) results.push({
      platform: site.name, url: '', category: site.category, status: phase === 'cancelled' ? 'cancelled' : 'error', message,
    })
  }
  return { ...run, phase, results, finishedAt: now, error: phase === 'error' ? message : null }
}

export function cancelRun(run: Run, catalog: Catalog, now: string): Run {
  return activeRun(run) ? finishRun(run, catalog, now, 'cancelled', 'Cancelled before a result arrived.') : run
}

export function applyEvent(run: Run, event: unknown, catalog: Catalog, now: string): Run {
  if (!activeRun(run) || !record(event) || event.id !== run.id) return run
  if (event.type === 'result') {
    const platform = event.platform
    if (!shortString(platform) || !validStatus(event.status) || !run.sites.includes(platform) ||
      run.results.some(r => r.platform === platform)) return run
    const site = catalog.sites.find(s => s.name === platform)
    if (!site) return run
    const result: Result = { platform, url: safeUrl(event.url), status: event.status, category: site.category,
      message: typeof event.message === 'string' ? event.message.slice(0, 2048) : '' }
    return { ...run, results: [...run.results, result], checked: run.checked + (result.status === 'cancelled' ? 0 : 1) }
  }
  if (event.type === 'done' && run.phase === 'cancelling') return cancelRun(run, catalog, now)
  if (event.type === 'done' && run.results.length === run.sites.length) return finishRun(run, catalog, now, 'complete', '')
  if (event.type !== 'error' && event.type !== 'done') return run
  const message = event.type === 'error' && shortString(event.message) ? event.message : 'The engine stopped before all platforms reported.'
  return finishRun(run, catalog, now, 'error', message)
}

function boundedInt(value: unknown, max: number, fallback: number): number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 1 && value <= max ? value : fallback
}

export function parseSettings(input: unknown): Settings {
  const value = record(input) ? input : {}
  return {
    rememberPreferences: value.rememberPreferences === true,
    timeout: boundedInt(value.timeout, 60, 10), concurrency: boundedInt(value.concurrency, 20, 8),
    saveHistory: value.saveHistory === true, defaultMode: value.defaultMode === 'full' ? 'full' : 'quick',
    theme: value.theme === 'light' || value.theme === 'system' ? value.theme : 'dark',
    density: value.density === 'compact' ? 'compact' : 'comfortable',
    disabledSites: Array.isArray(value.disabledSites) ? [...new Set(value.disabledSites.filter(shortString))] : [],
  }
}

function isDate(input: unknown): input is string {
  return typeof input === 'string' && input.length <= 40 && Number.isFinite(Date.parse(input))
}
function parseSavedRun(value: unknown): Run | null {
  if (!record(value) || !shortString(value.id) || !validUsername(value.username) || !isDate(value.startedAt) ||
    !isDate(value.finishedAt) || (value.mode !== 'quick' && value.mode !== 'full') ||
    (value.phase !== 'complete' && value.phase !== 'cancelled' && value.phase !== 'error') ||
    (value.error !== null && typeof value.error !== 'string') || !Array.isArray(value.sites) ||
    !value.sites.length || !value.sites.every(shortString) || !Array.isArray(value.results) ||
    value.results.length !== value.sites.length) return null
  const remaining = new Set(value.sites)
  if (remaining.size !== value.sites.length) return null
  const results: Result[] = []
  for (const row of value.results) {
    if (!record(row) || !shortString(row.platform) || !remaining.delete(row.platform) ||
      !shortString(row.category) || !validStatus(row.status) || typeof row.message !== 'string') return null
    results.push({ platform: row.platform, category: row.category, status: row.status,
      url: safeUrl(row.url), message: row.message.slice(0, 2048) })
  }
  // Older saved reports predate the explicit count. Unreported rows have no URL.
  const checked = typeof value.checked === 'number' && Number.isInteger(value.checked) &&
    value.checked >= 0 && value.checked <= results.length ? value.checked :
    results.filter(r => r.status !== 'cancelled' && (r.status !== 'error' || !!r.url)).length
  return { id: value.id, username: value.username, startedAt: value.startedAt, finishedAt: value.finishedAt, checked,
    mode: value.mode, phase: value.phase, sites: [...value.sites], results, error: value.error }
}

export function parseHistory(value: unknown): Run[] {
  if (!Array.isArray(value)) return []
  const runs: Run[] = []
  for (const entry of value) {
    const run = parseSavedRun(entry)
    if (run && !runs.some(r => r.id === run.id)) runs.push(run)
    if (runs.length >= historyLimit) break
  }
  return runs
}

function csvCell(value: string): string {
  const guarded = /^\s*[=+@-]|^[\t\r\n]/.test(value) ? "'" + value : value
  return '"' + guarded.replaceAll('"', '""') + '"'
}
function htmlText(value: string): string {
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;')
}

export function formatExport(run: Run, format: ExportFormat): string {
  if (format === 'json') return JSON.stringify(run, null, 2) + '\n'
  const columns = ['Username', 'Platform', 'Category', 'Status', 'Profile URL', 'Message']
  const rows = run.results.map(r => [run.username, r.platform, r.category, r.status, safeUrl(r.url), r.message])
  if (format === 'csv') {
    const records = [[...columns, 'Search started (UTC)'], ...rows.map(row => [...row, run.startedAt])]
    return records.map(row => row.map(csvCell).join(',')).join('\r\n') + '\r\n'
  }
  const header = columns.map(s => '<th scope="col">' + s + '</th>').join('')
  const body = rows.map(row => '<tr>' + row.map(s => '<td>' + htmlText(s) + '</td>').join('') + '</tr>').join('\n')
  return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>HuntWick search report</title><style>body{font:1rem system-ui;margin:2rem;color:#18212b}table{border-collapse:collapse}td,th{padding:.5rem;border:1px solid #ccd1d5;text-align:left;overflow-wrap:anywhere}</style></head><body>' +
    '<h1>HuntWick search report</h1><p>Username: ' + htmlText(run.username) + '</p><p>Started: ' + htmlText(run.startedAt) +
    ' · Status: ' + htmlText(run.phase) + ' · Results: ' + rows.length + ' / ' + run.sites.length +
    '</p><table><thead><tr>' + header + '</tr></thead><tbody>' + body + '</tbody></table></body></html>\n'
}

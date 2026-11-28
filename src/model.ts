export type Mode = 'quick' | 'full'
export type Status = 'found' | 'possible' | 'provider_match' | 'conflict' | 'not_found' | 'inconclusive' | 'timed_out' | 'blocked' | 'cancelled' | 'error'
export type Phase = 'running' | 'cancelling' | 'complete' | 'cancelled' | 'error'
export type ExportFormat = 'csv' | 'json' | 'html'

export const engines = ['sherlock','enhanced','maigret','deep'] as const
export type Engine = typeof engines[number]
export function eligible(site: Site, engine: Engine) {
  return site.engines?.includes(engine) ?? (!site.nativeOnly || engine !== 'sherlock')
}
export interface Site {
  engines?: Engine[]
  name: string
  url: string
  category: string
  federated?: boolean
  nativeOnly?: boolean
  quick: boolean
}
/** A qualified handle selects a known instance; it never supplies a network endpoint. */
export function federatedSelection(input: string, engine: Engine, sites: Site[]) {
  if (engine !== 'deep' && engine !== 'maigret') return null
  const address = /^@?([A-Za-z0-9_]{1,64})@([A-Za-z0-9.-]+)$/.exec(input.trim())
  if (!address) return null
  return {
    username: address[1],
    sites: sites.filter(site => site.federated && new URL(site.url).hostname === address[2].toLowerCase()),
  }
}

export interface Catalog {
  version: string
  databaseVersion: string
  updatedAt: string
  sites: Site[]
  unavailable?: { name: string; reason: string }[]
}
export interface Result {
  platform: string
  url: string
  category: string
  status: Status
  catalogVersion?: string
  sources?: {provider:string; status:Status; verdict?:string; http?:number}[]
  provider?: string
  verdict?: string
  http?: number
  elapsedMs?: number
  reason?: string
  message: string
}
export interface Run {
  engine?: Engine
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
  providerMode: Engine
  retryTransient: boolean
  scanSound: boolean
  radarSound: boolean
  radarVolume: number
  includePrereleases: boolean
  autoUpdates: boolean
  adultConsent: boolean
  includeNsfw: boolean
  includeExcluded: boolean
  rememberPreferences: boolean
  timeout: number
  concurrency: number
  saveHistory: boolean
  defaultMode: Mode
  theme: 'dark' | 'light' | 'system'
  density: 'compact' | 'comfortable'
  disabledSites: string[]
}

export const statusLabels: Record<Status, string> = {
  provider_match: 'Provider Match', conflict: 'Conflicting Evidence', found: 'Verified Match', possible: 'Possible Match', not_found: 'Not found', blocked: 'Blocked',
  timed_out: 'Timed out', inconclusive: 'Inconclusive', error: 'Error', cancelled: 'Cancelled',
}
const statuses: ReadonlySet<string> = new Set(Object.keys(statusLabels))
export type ResultView = 'balanced' | 'strict' | 'diagnostics' | 'all'

export function countStatuses(rows: Result[]): Record<Status, number> {
  const counts = { provider_match: 0, conflict: 0, found: 0, possible: 0, not_found: 0, blocked: 0, timed_out: 0, inconclusive: 0, error: 0, cancelled: 0 }
  for (const row of rows) counts[row.status]++
  return counts
}
export function visibleIn(status: Status, view: ResultView) {
  const match = status === 'found' || status === 'possible' || status === 'provider_match' || status === 'conflict'
  if (view === 'balanced') return match
  if (view === 'strict') return status === 'found'
  if (view === 'diagnostics') return !match
  return true
}
export function matchLinks(rows: Result[], level: 'found' | 'possible'): string {
  return [...new Set(rows.filter(row => row.status === level).map(row => safeUrl(row.url)).filter(Boolean))].join('\n')
}
export const historyLimit = 20

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
function provenance(row: {sources?:unknown; provider?:unknown; verdict?:unknown; catalogVersion?:unknown; http?:unknown; elapsedMs?:unknown}) {
  return {
    ...(Array.isArray(row.sources) ? {sources:row.sources.filter(s=>record(s) && shortString(s.provider) && validStatus(s.status)).map(s=>({provider:s.provider,status:s.status,...(shortString(s.verdict)?{verdict:s.verdict}:{}),...(Number.isInteger(s.http)?{http:s.http}:{})}))} : {}),
    ...(shortString(row.catalogVersion) ? {catalogVersion:row.catalogVersion} : {}),
    ...(shortString(row.provider) ? {provider:row.provider} : {}),
    ...(shortString(row.verdict) ? {verdict:row.verdict} : {}),
    ...(typeof row.http === 'number' && Number.isInteger(row.http) && row.http >= 100 && row.http <= 599 ? {http:row.http} : {}),
    ...(typeof row.elapsedMs === 'number' && Number.isSafeInteger(row.elapsedMs) && row.elapsedMs >= 0 ? {elapsedMs:row.elapsedMs} : {}),
  }
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
    return { ...(s.federated === true ? {federated:true} : {}), ...(Array.isArray(s.engines) && s.engines.length ? {engines:s.engines.filter(e=>engines.includes(e))} : {}), ...(s.nativeOnly === true ? {nativeOnly:true} : {}), name: s.name, category: s.category, quick: s.quick, url: safeUrl(s.url) }
  })
  const catalog: Catalog = { version: value.version, databaseVersion: value.databaseVersion, updatedAt: value.updatedAt, sites }
  if (value.unavailable === undefined) return catalog
  if (!Array.isArray(value.unavailable)) throw new Error('The unavailable platform list is invalid.')
  catalog.unavailable = value.unavailable.map((entry: unknown) => {
    if (!record(entry) || !shortString(entry.name) || !shortString(entry.reason) || seen.has(entry.name)) {
      throw new Error('The engine returned an invalid unavailable platform.')
    }
    seen.add(entry.name)
    return { name: entry.name, reason: entry.reason }
  })
  return catalog
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
    const result: Result = { ...provenance(event), platform, url: safeUrl(event.url), status: event.status, category: site.category,
      ...(shortString(event.reason) ? { reason: event.reason } : {}),
      message: typeof event.message === 'string' ? event.message.slice(0, 2048) : ({
        possible: 'Account-specific evidence was incomplete. Review the public page.',
        blocked: 'The service restricted access or rate limited the request.',
        timed_out: 'The platform check exceeded its time limit.',
        error: 'The platform check could not be completed.',
        inconclusive: 'The check returned insufficient evidence or the platform rejected this username format.',
      } as Partial<Record<Status, string>>)[event.status] ?? '' }
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
    providerMode: engines.includes(value.providerMode as Engine) ? value.providerMode as Engine : 'deep', retryTransient: value.retryTransient === true,
    includePrereleases: value.includePrereleases === true,
    autoUpdates: value.autoUpdates !== false,
    adultConsent: value.adultConsent === true || value.includeNsfw === true,
    includeNsfw: value.includeNsfw === true, includeExcluded: value.includeExcluded === true,
    scanSound: value.scanSound === true,
    radarSound: value.radarSound !== false,
    radarVolume: typeof value.radarVolume === 'number' && Number.isFinite(value.radarVolume) ? Math.max(0,Math.min(100,value.radarVolume)) : 20,
    rememberPreferences: value.rememberPreferences === true,
    timeout: boundedInt(value.timeout, 60, 10), concurrency: boundedInt(value.concurrency, 20, 8),
    saveHistory: value.saveHistory === true, defaultMode: value.defaultMode === 'quick' ? 'quick' : 'full',
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
      !shortString(row.category) || !validStatus(row.status) || (row.message !== undefined && typeof row.message !== 'string')) return null
    results.push({ ...provenance(row), platform: row.platform, category: row.category, status: row.status,
      ...(shortString(row.reason) ? { reason: row.reason } : {}),
      url: safeUrl(row.url), message: typeof row.message === 'string' ? row.message.slice(0, 2048) : '' })
  }
  // Older saved reports predate the explicit count. Unreported rows have no URL.
  const checked = typeof value.checked === 'number' && Number.isInteger(value.checked) &&
    value.checked >= 0 && value.checked <= results.length ? value.checked :
    results.filter(r => r.status !== 'cancelled' && (r.status !== 'error' || !!r.url)).length
  return { ...(engines.includes(value.engine as Engine) ? {engine:value.engine as Engine} : {}), id: value.id, username: value.username, startedAt: value.startedAt, finishedAt: value.finishedAt, checked,
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
  if (format === 'json') return JSON.stringify({ ...run, statusLabels, counts: countStatuses(run.results) }, null, 2) + '\n'
  const columns = ['Username', 'Platform', 'Category', 'Status', 'Profile URL', 'Message']
  if (format === 'csv') {
    const records = [[...columns, 'Search started (UTC)', 'Result label', 'Reason', 'Provider', 'Provider verdict'],
      ...run.results.map(r => [run.username, r.platform, r.category, r.status, safeUrl(r.url), r.message,
        run.startedAt, statusLabels[r.status], r.reason ?? '',r.provider ?? '',r.verdict ?? ''])]
    return records.map(row => row.map(csvCell).join(',')).join('\r\n') + '\r\n'
  }
  const header = [...columns, 'Reason','Provider','Provider verdict'].map(s => '<th scope="col">' + s + '</th>').join('')
  const body = run.results.map(r => [run.username, r.platform, r.category, statusLabels[r.status], safeUrl(r.url), r.message, r.reason ?? '',r.provider ?? '',r.verdict ?? ''])
    .map(row => '<tr>' + row.map(s => '<td>' + htmlText(s) + '</td>').join('') + '</tr>').join('\n')
  return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>HuntWick search report</title><style>body{font:1rem system-ui;margin:2rem;color:#18212b}table{border-collapse:collapse}td,th{padding:.5rem;border:1px solid #ccd1d5;text-align:left;overflow-wrap:anywhere}</style></head><body>' +
    '<h1>HuntWick search report</h1><p>Username: ' + htmlText(run.username) + '</p><p>Started: ' + htmlText(run.startedAt) +
    ' · Status: ' + htmlText(run.phase) + ' · Results: ' + run.results.length + ' / ' + run.sites.length +
    '</p><table><thead><tr>' + header + '</tr></thead><tbody>' + body + '</tbody></table></body></html>\n'
}

/** Share only recognized transport measurements. Older history may contain free text. */
export function diagnosticReport(run: Run) {
  const providers = new Set(['Sherlock Original', 'HuntWick public lookup', 'Maigret'])
  return JSON.stringify({mode:run.mode, engine:run.engine, selected:run.sites.length,
    completed:run.checked, counts:countStatuses(run.results), checks:run.results.map(row=>{
    const http=/^Sherlock: (Claimed|Available|Unknown|Illegal|WAF)\. HTTP (\d{3})\. Headers: (\d+\.\d+) s\. Total: (\d+\.\d+) s\.$/.exec(row.message)
    const failure=/^(Connect timeout|Response timeout|Body timeout|Connection failure|TLS failure) after (\d+\.\d+) s\.$/.exec(row.message)
    return {platform:row.platform,status:row.status,...(row.provider && providers.has(row.provider) ? {provider:row.provider} : {}),
      ...(row.sources ? {sources:row.sources.filter(s => providers.has(s.provider) && validStatus(s.status))
        .map(s => ({provider:s.provider, status:s.status}))} : {}),
      ...(row.verdict && /^(Claimed|Available|Illegal|Unknown|WAF|API identity matched|Identity unavailable|Invalid handle|Numeric profile redirect|Empty user lookup|ProfileNotFound|Request failed|Connection failure|TLS failure|DNS failure|Proxy connection failure|Timeout|HTTP [1-5][0-9]{2})$/.test(row.verdict) ? {verdict:row.verdict} : {}),
      ...(row.http ? {http:row.http} : {}),...(row.elapsedMs !== undefined ? {elapsedMs:row.elapsedMs} : {}),...(http?{upstream:http[1],http:Number(http[2]),headersSeconds:Number(http[3]),totalSeconds:Number(http[4])}:{}),
      ...(failure?{failure:failure[1],totalSeconds:Number(failure[2])}:{})}
  })},null,2)
}

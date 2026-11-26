import { playCue, stopRadar } from './ui/radarAudio'
import {
  eligible, activeRun, applyEvent, cancelRun, createRun, diagnosticReport, formatExport, historyLimit, parseCatalog, parseHistory,
  parseSettings, safeUrl, selectSites, validUsername,
} from './model'
import type { Catalog, Engine, ExportFormat, Mode, Run, Settings } from './model'

interface SearchRequest {
  id: string
  username: string
  sites: string[]
  concurrency: number
  timeout: number
}
export interface Bridge {
  hosted?: boolean
  close?(): void
  desktop: boolean
  catalog(policy: Pick<Settings, 'includeNsfw' | 'includeExcluded'>): Promise<unknown>
  listen(listener: (event: unknown) => void): Promise<() => void>
  start(request: SearchRequest): Promise<void>
  cancel(id: string): Promise<void>
  open(url: string): Promise<void>
  save(format: ExportFormat, contents: string): Promise<boolean>
}
export type LocalStore = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>
interface Snapshot {
  catalog: Catalog | null
  run: Run | null
  settings: Settings
  history: Run[]
  ready: boolean
  hosted: boolean
  maxConcurrency: number
  maxTimeout: number
  desktop: boolean
  error: string | null
}
const settingsKey = 'huntwick.preferences.v1'
const historyKey = 'huntwick.history.v1'
function read(store: LocalStore | null, key: string): unknown {
  try { return JSON.parse(store?.getItem(key) ?? 'null') }
  catch { return null }
}
function message(error: unknown): string {
  if (typeof error === 'string') return error.slice(0, 1024)
  if (error instanceof Error) return error.message.slice(0, 1024)
  return 'The operation could not be completed.'
}
const now = () => new Date().toISOString()

export class HuntWickSession {
  private state: Snapshot
  private subscribers = new Set<() => void>()
  private generation = 0
  private unlisten: (() => void) | null = null
  private eligibleHistoryId: string | null = null
  private launching: Promise<void> | null = null

  private settings(input: unknown): Settings {
    const settings = parseSettings(input)
    if (this.bridge.hosted) {
      settings.providerMode = "sherlock"
      if (!input) settings.radarSound = false
      settings.timeout = Math.min(20, settings.timeout)
      settings.concurrency = Math.min(2, settings.concurrency)
    }
    return settings
  }
  constructor(private bridge: Bridge, private store: LocalStore | null) {
    this.state = {
      catalog: null, run: null, history: parseHistory(read(store, historyKey)), settings: this.settings(read(store, settingsKey)),
      hosted: !!bridge.hosted, maxTimeout: bridge.hosted ? 20 : 60, maxConcurrency: bridge.hosted ? 2 : 20,
      desktop: bridge.desktop, ready: false, error: null,
    }
  }

  snapshot = () => this.state
  subscribe = (listener: () => void) => {
    this.subscribers.add(listener)
    return () => { this.subscribers.delete(listener) }
  }
  private update(patch: Partial<Snapshot>) {
    this.state = { ...this.state, ...patch }
    for (const listener of this.subscribers) listener()
  }

  disconnect = () => {
    stopRadar()
    this.generation++
    this.unlisten?.()
    this.unlisten = null
    this.bridge.close?.()
    if (this.bridge.hosted) {
      const { run, catalog } = this.state
      if (run && catalog && activeRun(run)) this.acceptRun(cancelRun(run, catalog, now()))
      this.update({ ready: false })
    }
  }
  connect = async () => {
    if (activeRun(this.state.run)) return
    this.disconnect()
    const generation = this.generation
    this.update({ ready: false, error: null })
    try {
      const catalog = parseCatalog(await this.bridge.catalog({ includeNsfw: this.state.settings.includeNsfw, includeExcluded: this.state.settings.includeExcluded }))
      if (this.generation !== generation) return
      if (this.bridge.desktop || this.bridge.hosted) {
        const unlisten = await this.bridge.listen(event => {
          if (this.generation !== generation || !this.state.run) return
          const before = this.state.run
          const after = applyEvent(before, event, catalog, now())
          const latest = after.results.at(-1)
          if (after.results.length > before.results.length && this.state.settings.radarSound &&
              latest && ['found','possible','provider_match','conflict'].includes(latest.status)) {
            const cue = latest.status === 'found' ? 'verified' : latest.status === 'possible' ? 'possible' : latest.status === 'conflict' ? 'conflict' : 'provider'
            playCue(cue, this.state.settings.radarVolume)
          }
          this.acceptRun(after)
        })
        if (generation !== this.generation) { unlisten(); return }
        this.unlisten = unlisten
      }
      this.update({ catalog, ready: true })
    } catch (e) {
      if (generation === this.generation) this.update({ error: message(e) })
    }
  }

  private persist(key: string, value: unknown): boolean {
    try {
      if (!this.store) throw new Error()
      if (value === null) this.store.removeItem(key)
      else this.store.setItem(key, JSON.stringify(value))
      return true
    } catch {
      this.update({ error: 'Local storage is unavailable or full. Changes could not be saved to this device.' })
      return false
    }
  }
  private setHistory(history: Run[]) {
    if (this.persist(historyKey, history.length ? history : null)) this.update({ history })
  }
  private acceptRun(run: Run) {
    if (this.state.run === run) return
    this.update({ run, ...(run.error ? { error: run.error } : {}) })
    if (activeRun(run)) return
    if (run.id === this.eligibleHistoryId && this.state.settings.saveHistory) {
      this.setHistory([run, ...this.state.history.filter(r => r.id !== run.id)].slice(0, historyLimit))
    }
    this.eligibleHistoryId = null
  }

  clearError = () => this.update({ error: null })
  clearRun = () => {
    if (!activeRun(this.state.run)) this.update({ run: null, error: null })
  }
  updateSettings = (patch: Partial<Settings>) => {
    const settings = this.settings({ ...this.state.settings, ...patch })
    if (!settings.saveHistory) this.eligibleHistoryId = null
    const reload = settings.includeNsfw !== this.state.settings.includeNsfw || settings.includeExcluded !== this.state.settings.includeExcluded
    if (reload && activeRun(this.state.run)) return
    this.update({ settings })
    if (reload) void this.connect()
    const { timeout, concurrency, defaultMode, ...appSettings } = settings
    this.persist(settingsKey, settings.rememberPreferences ? { ...appSettings, timeout, concurrency, defaultMode } : appSettings)
  }
  loadHistory = (id: string) => {
    if (activeRun(this.state.run)) return
    const run = this.state.history.find(r => r.id === id)
    if (run) this.update({ run, error: null })
  }
  deleteHistory = (id: string) => this.setHistory(this.state.history.filter(r => r.id !== id))
  clearHistory = () => this.setHistory([])
  clearLocalData = (): boolean => {
    if (activeRun(this.state.run)) return false
    this.eligibleHistoryId = null
    this.clearError()
    const historyCleared = this.persist(historyKey, null)
    const resetCatalog = this.state.settings.includeNsfw || this.state.settings.includeExcluded
    const settingsCleared = this.persist(settingsKey, null)
    this.update({
      run: null,
      ...(historyCleared ? { history: [] } : {}),
      ...(settingsCleared ? { settings: this.settings(null) } : {}),
    })
    if (settingsCleared && resetCatalog) void this.connect()
    return historyCleared && settingsCleared
  }

  start = async (username: string, mode: Mode, selected?: string[], retryEngine?: Engine) => {
    if (activeRun(this.state.run)) return
    if (!validUsername(username)) { this.update({ error: 'Enter a username of 1–64 letters, digits, dots, dashes or underscores.' }); return }
    const { catalog, settings, ready, desktop } = this.state
    if (!desktop && !this.state.hosted) { this.update({ error: 'Open HuntWick on your desktop to run a search.' }); return }
    if (!catalog || !ready) { this.update({ error: 'Wait for the platform catalog to load.' }); return }
    const engine = retryEngine ?? settings.providerMode
    const sites = selectSites(catalog, mode, settings.disabledSites, selected).filter(s=>eligible(s, engine))
    if (!sites.length) { this.update({ error: 'Enable at least one platform for this search.' }); return }
    const run = createRun(crypto.randomUUID(), username, mode, sites, now())
    if (!this.bridge.hosted) run.engine = engine
    this.eligibleHistoryId = settings.saveHistory ? run.id : null
    this.update({ run, error: null })
    const request = { ...(!this.bridge.hosted && engine !== "sherlock" ? {providerMode:engine} : {}),
      ...(!this.bridge.hosted && settings.retryTransient ? {retryTransient:true} : {}), id: run.id, username, sites: run.sites, timeout: settings.timeout, concurrency: settings.concurrency }
    const launch = this.bridge.start(request)
    this.launching = launch
    try {
      await launch
    } catch (e) {
      const current = this.state.run
      if (current?.id === run.id) this.acceptRun(applyEvent(current, { type: 'error', id: run.id, message: message(e) }, catalog, now()))
    } finally {
      if (this.launching === launch) this.launching = null
    }
  }
  cancel = async () => {
    const { run, catalog } = this.state
    if (!run || !catalog || run.phase !== 'running') return
    this.update({ run: { ...run, phase: 'cancelling' } })
    try {
      if (!this.bridge.hosted) await this.launching
      if (this.state.run?.id !== run.id || !activeRun(this.state.run)) return
      await this.bridge.cancel(run.id)
      const current = this.state.run
      if (current?.id === run.id) this.acceptRun(cancelRun(current, catalog, now()))
    } catch (e) {
      const current = this.state.run
      if (current?.id === run.id && current.phase === 'cancelling') {
        this.update({ run: { ...current, phase: 'running' }, error: message(e) })
      }
    }
  }
  openUrl = async (raw: string) => {
    const url = safeUrl(raw)
    if (!url) { this.update({ error: 'This profile link is unavailable.' }); return }
    try { await this.bridge.open(url) }
    catch (e) { this.update({ error: message(e) }) }
  }
  exportRun = async (format: ExportFormat | 'diagnostics') => {
    const { run } = this.state
    if (!run || !run.results.length) return
    try { await (format === 'diagnostics' ? this.bridge.save('json', diagnosticReport(run)) : this.bridge.save(format, formatExport(run, format))) }
    catch (e) { this.update({ error: message(e) }) }
  }
}

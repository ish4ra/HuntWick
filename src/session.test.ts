import { describe, expect, it } from 'vitest'
import { HuntWickSession } from './session'
import type { Bridge, LocalStore } from './session'

const rawCatalog = { type: 'catalog', version: '1', databaseVersion: '2', updatedAt: '2026-01-01', sites: [
  { name: 'Forum', category: 'Community', quick: true, url: 'https://forum.example/' },
  { name: 'Archive', category: 'Media', quick: false, url: 'https://archive.example/' },
] }

function fixture() {
  const data = new Map<string, string>()
  const storage: LocalStore = { getItem: key => data.get(key) ?? null, setItem: (key, value) => {data.set(key, value)}, removeItem: key => {data.delete(key)} }
  let receiver: ((e: unknown) => void) | undefined
  const requests: { id: string; username: string; sites: string[]; timeout: number; concurrency: number }[] = []
  const bridge: Bridge = {
    desktop: true, catalog: async () => rawCatalog,
    listen: async fn => { receiver = fn; return () => { receiver = undefined } },
    start: async request => { requests.push(request) }, cancel: async () => {}, open: async () => {}, save: async () => true,
  }
  const session = new HuntWickSession(bridge, storage)
  function finish() {
    receiver?.({ type: 'result', id: requests[0].id, platform: 'Forum', url: 'https://forum.example/alpha', status: 'found' })
    receiver?.({ type: 'done', id: requests[0].id })
  }
  return { session, bridge, storage, data, requests, finish }
}

describe('desktop session', () => {
  it('submits scoped native requests once and keeps default searches in memory', async () => {
    const { session, requests, data, finish } = fixture()
    await session.connect()
    await Promise.all([session.start('alpha', 'quick'), session.start('beta', 'full')])
    expect(requests).toEqual([{ id: expect.any(String), username: 'alpha', sites: ['Forum'], timeout: 10, concurrency: 8 }])
    finish()
    expect(session.snapshot().run?.phase).toBe('complete')
    expect(session.snapshot().history).toEqual([])
    expect([...data.values()].join('')).not.toContain('alpha')
  })
  it('preserves earlier opted-in history until explicitly cleared', async () => {
    const { session, bridge, storage, data, finish } = fixture()
    await session.connect()
    session.updateSettings({ saveHistory: true })
    await session.start('alpha', 'quick')
    finish()
    const newSession = new HuntWickSession(bridge, storage)
    expect(newSession.snapshot().history.map(r => r.username)).toEqual(['alpha'])
    newSession.updateSettings({ saveHistory: false })
    expect(newSession.snapshot().history.map(r => r.username)).toEqual(['alpha'])
    newSession.clearHistory()
    expect([...data.values()].join('')).not.toContain('alpha')
    expect(new HuntWickSession(bridge, storage).snapshot().history).toEqual([])
  })
  it('persists search limits and mode only while requested, independently of display and platform settings', () => {
    const { session, bridge, storage } = fixture()
    const reopen = () => new HuntWickSession(bridge, storage).snapshot().settings
    session.updateSettings({ timeout: 33, concurrency: 19, defaultMode: 'full', density: 'compact', disabledSites: ['Archive'] })
    expect(session.snapshot().settings.timeout).toBe(33)
    expect(reopen()).toMatchObject({ timeout: 10, concurrency: 8, defaultMode: 'quick', density: 'compact', disabledSites: ['Archive'] })
    session.updateSettings({ rememberPreferences: true })
    expect(reopen()).toMatchObject({ timeout: 33, concurrency: 19, defaultMode: 'full' })
    session.updateSettings({ rememberPreferences: false })
    expect(reopen()).toMatchObject({ timeout: 10, concurrency: 8, defaultMode: 'quick' })
    expect(session.snapshot().settings.timeout).toBe(33)
  })
  it('resets HuntWick data and in-memory results without clearing unrelated storage', async () => {
    const { session, data, bridge, storage, finish } = fixture()
    data.set('other-product', 'keep')
    await session.connect()
    session.updateSettings({ saveHistory: true, rememberPreferences: true, timeout: 42 })
    await session.start('alpha', 'quick')
    expect(session.clearLocalData()).toBe(false)
    finish()
    expect(session.clearLocalData()).toBe(true)
    expect(Array.from(data.entries())).toEqual([['other-product', 'keep']])
    expect(session.snapshot()).toMatchObject({ run: null, history: [], ready: true, settings: { saveHistory: false, timeout: 10 } })
    expect(new HuntWickSession(bridge, storage).snapshot().settings.rememberPreferences).toBe(false)
  })
  it('never saves an active search after consent is revoked and restored', async () => {
    const { session, finish } = fixture()
    await session.connect()
    session.updateSettings({ saveHistory: true })
    await session.start('alpha', 'quick')
    session.updateSettings({ saveHistory: false })
    session.updateSettings({ saveHistory: true })
    finish()
    expect(session.snapshot().history).toEqual([])
  })
  it('finishes in-flight cancellation and allows a subsequent run', async () => {
    const { session, requests } = fixture()
    await session.connect()
    await session.start('alpha', 'full')
    await session.cancel()
    expect(session.snapshot().run?.results.map(r => r.status)).toEqual(['cancelled', 'cancelled'])
    await session.start('beta', 'quick')
    expect(requests.map(r => r.username)).toEqual(['alpha', 'beta'])
  })
  it('does not submit from a browser preview or fabricate results', async () => {
    const { bridge, storage, requests } = fixture()
    const session = new HuntWickSession({ ...bridge, desktop: false }, storage)
    await session.connect()
    await session.start('alpha', 'quick')
    expect(requests).toEqual([])
    expect(session.snapshot().error).toMatch(/desktop/i)
    expect(session.snapshot().run).toBeNull()
  })
  it('restores readiness after a failed native launch', async () => {
    const { bridge, session } = fixture()
    bridge.start = async () => { throw new Error('Missing engine executable') }
    await session.connect()
    await session.start('alpha', 'quick')
    expect(session.snapshot().run).toMatchObject({ phase: 'error', error: 'Missing engine executable' })
    expect(session.snapshot().error).toMatch(/Missing engine/)
  })
})

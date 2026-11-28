import { describe, expect, it } from 'vitest'
import {
  applyEvent, cancelRun, createRun, formatExport, parseCatalog, parseHistory,
  parseSettings, safeUrl, selectSites, validUsername,
} from './model'
import type { Catalog, Run, Site } from './model'

const sites: Site[] = [
  { name: 'Forum', category: 'Community', url: 'https://forum.example/', quick: true },
  { name: 'Archive', category: 'Media', url: 'https://archive.example/', quick: false },
]
const catalog: Catalog = { version: 'v1', databaseVersion: 'v2', updatedAt: '2026-11-20', sites }
const now = '2026-11-22T00:00:00.000Z'
const later = '2026-11-22T00:01:00.000Z'
const fresh = (): Run => createRun('id', 'test.user', 'full', sites, now)
const result = { type: 'result', id: 'id', platform: 'Forum', url: 'https://forum.example/test.user', status: 'found', message: 'Matched' }
const collected = () => applyEvent(fresh(), result, catalog, later)

describe('catalog and input', () => {
  it('accepts a native catalog with or without its type tag', () => {
    expect(parseCatalog(catalog)).toEqual(catalog)
    expect(parseCatalog({ type: 'catalog', ...catalog })).toEqual(catalog)
    expect(() => parseCatalog({ ...catalog, sites: [sites[0], sites[0]] })).toThrow()
  })
  it('honors selection, quick scope, and disabled platforms', () => {
    expect(selectSites(catalog, 'quick', []).map(s => s.name)).toEqual(['Forum'])
    expect(selectSites(catalog, 'full', ['Forum']).map(s => s.name)).toEqual(['Archive'])
    expect(selectSites(catalog, 'full', ['Archive'], ['Archive'])).toEqual([])
  })
  it.each(['.', '..', ' a', 'ab/c', 'a\nb', 'a'.repeat(65), ''])('rejects unsupported username %j', name => {
    expect(validUsername(name)).toBe(false)
  })
  it('accepts supported punctuation and the maximum length', () => {
    expect(validUsername('a._-9')).toBe(true)
    expect(validUsername('x'.repeat(64))).toBe(true)
  })
  it.each(['http://example.org/', 'javascript:alert(1)', 'file:///tmp/test', 'https://user@example.org/', 'https://127.0.0.1/', 'https://localhost/', 'https://[::1]/', 'https://example.org/\nfoo'])('rejects unsafe links %j', input => {
    expect(safeUrl(input)).toBe('')
  })
})

describe('run lifecycle', () => {
  it('ignores old, unknown and duplicate results', () => {
    const run = fresh()
    expect(applyEvent(run, { ...result, id: 'older' }, catalog, later)).toBe(run)
    expect(applyEvent(run, { ...result, platform: 'Injected' }, catalog, later)).toBe(run)
    const updated = collected()
    expect(updated.results).toEqual([{ platform: 'Forum', url: result.url, status: 'found', message: 'Matched', category: 'Community' }])
    expect(applyEvent(updated, result, catalog, later)).toBe(updated)
    expect(applyEvent(run, { ...result, status: 'waiting' }, catalog, later)).toBe(run)
  })
  it('preserves a status without exposing an unsafe profile link', () => {
    expect(applyEvent(fresh(), { ...result, url: 'javascript:test()' }, catalog, later).results[0].url).toBe('')
  })
  it('marks interrupted work explicitly and preserves earlier results', () => {
    const run = applyEvent(collected(), { id: 'id', type: 'done' }, catalog, later)
    expect(run.checked).toBe(1)
    expect(run.phase).toBe('error')
    expect(run.results.map(r => r.status)).toEqual(['found', 'error'])
    expect(run.finishedAt).toBe(later)
    expect(applyEvent(run, result, catalog, later)).toBe(run)
  })
  it('cancels only outstanding platforms and ignores late events', () => {
    const run = cancelRun(collected(), catalog, later)
    expect(run.checked).toBe(1)
    expect(run.phase).toBe('cancelled')
    expect(run.results.map(r => r.status)).toEqual(['found', 'cancelled'])
    expect(applyEvent(run, { id: 'id', type: 'done' }, catalog, later)).toBe(run)
  })
  it('keeps a platform error and completes a fully accounted run', () => {
    const current = applyEvent(collected(), { ...result, platform: 'Archive', status: 'error' }, catalog, later)
    expect(applyEvent(current, { id: 'id', type: 'done' }, catalog, later).phase).toBe('complete')
  })
})

describe('reports and local preferences', () => {
  it('includes the original search time in each exported CSV row', () => {
    const run = cancelRun(collected(), catalog, later)
    const lines = formatExport(run, 'csv').trimEnd().split('\r\n')
    expect(lines[0]).toContain('"Search started (UTC)"')
    expect(lines.slice(1)).toHaveLength(run.results.length)
    for (const line of lines.slice(1)) expect(line).toContain('"' + now + '"')
  })
  it('escapes HTML and CSV formula cells and preserves original JSON data', () => {
    const run = cancelRun(collected(), catalog, later)
    run.results[0].message = '  =SUM(1,2)"<script>'
    const csv = formatExport(run, 'csv')
    expect(csv).toContain('"\'  =SUM(1,2)""<script>"')
    const html = formatExport(run, 'html')
    expect(html).toContain('&lt;script&gt;')
    expect(html).not.toContain('<script>')
    expect(JSON.parse(formatExport(run, 'json')).results).toEqual(run.results)
  })
  it('includes prereleases only when explicitly enabled', () => {
    expect(parseSettings({}).includePrereleases).toBe(false)
    expect(parseSettings({includePrereleases: 'true'}).includePrereleases).toBe(false)
    expect(parseSettings({includePrereleases: true}).includePrereleases).toBe(true)
  })
  it('restores validated preferences and keeps history opt-in', () => {
    expect(parseSettings({ saveHistory: 'true', timeout: -1, concurrency: 40 })).toMatchObject({ saveHistory: false, timeout: 10, concurrency: 8 })
    expect(parseSettings({ saveHistory: true, timeout: 60, concurrency: 20, disabledSites: ['Forum', 'Forum', false] })).toMatchObject({ saveHistory: true, timeout: 60, concurrency: 20, disabledSites: ['Forum'] })
  })
  it('restores only completed, well-formed history, and cleans persisted URLs', () => {
    const finished = cancelRun(collected(), catalog, later)
    const stored = structuredClone(finished)
    stored.results[0].url = 'javascript:bad'
    expect(parseHistory([fresh(), {}, null, stored, stored])).toEqual([{ ...finished, results: [{ ...finished.results[0], url: '' }, finished.results[1]] }])
  })
})

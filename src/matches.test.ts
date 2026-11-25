import { describe, expect, it } from 'vitest'
import { applyEvent, countStatuses, createRun, formatExport, matchLinks, parseCatalog, parseHistory, selectSites, visibleIn } from './model'
import type { Catalog, Result, Status } from './model'

const site = { name: 'Forum', url: 'https://forum.example/', quick: true, category: 'Community' }
const catalog: Catalog = { version: '1', databaseVersion: '1', updatedAt: '2026-11-24', sites: [site] }
const now = '2026-11-24T12:00:00Z'
const statuses: Status[] = ['found', 'possible', 'not_found', 'blocked', 'timed_out', 'inconclusive', 'error', 'cancelled']
const rows: Result[] = statuses.map((status, i) => ({
  platform: 'Site ' + i, status, url: 'https://platform.example/p' + i, category: 'Social', message: '',
}))

describe('evidence in results and reports', () => {
  it('keeps each status distinct and filters match views without moving diagnostics into either match group', () => {
    expect(countStatuses([...rows, rows[1]])).toEqual({ provider_match: 0, conflict: 0, found: 1, possible: 2, not_found: 1, blocked: 1, timed_out: 1, inconclusive: 1, error: 1, cancelled: 1 })
    expect(statuses.filter(s => visibleIn(s, 'balanced'))).toEqual(['found', 'possible'])
    expect(statuses.filter(s => visibleIn(s, 'strict'))).toEqual(['found'])
    expect(statuses.filter(s => visibleIn(s, 'diagnostics'))).toEqual(['not_found', 'blocked', 'timed_out', 'inconclusive', 'error', 'cancelled'])
    expect(matchLinks(rows, 'found')).toBe('https://platform.example/p0')
    expect(matchLinks(rows, 'possible')).toBe('https://platform.example/p1')
  })
  it('preserves a possible match and its evidence in saved history and exports', () => {
    const run = createRun('fixture', 'fixture', 'quick', [site], now)
    const partial = applyEvent(run, { id: run.id, type: 'result', platform: site.name, url: site.url + 'fixture', status: 'possible', reason: 'marker_missing', message: 'Profile marker missing.' }, catalog, now)
    const done = applyEvent(partial, { id: run.id, type: 'done' }, catalog, now)
    expect(done.checked).toBe(1)
    expect(parseHistory([done])[0].results[0]).toMatchObject({ status: 'possible', reason: 'marker_missing', message: 'Profile marker missing.' })
    for (const format of ['csv', 'html'] as const) {
      expect(formatExport(done, format)).toContain('Possible Match')
      expect(formatExport(done, format)).toContain('Profile marker missing.')
      expect(formatExport(done, format)).toContain('marker_missing')
    }
    expect(JSON.parse(formatExport(done, 'json')).results[0].status).toBe('possible')
  })
  it('exposes exclusion reasons without ever selecting unavailable sites', () => {
    const unavailable = [{ name: 'Removed site', reason: 'The provider retired its public lookup.' }]
    const directory = parseCatalog({ ...catalog, unavailable })
    expect(directory.unavailable).toEqual(unavailable)
    expect(selectSites(directory, 'full', [], ['Removed site'])).toEqual([])
    expect(() => parseCatalog({ ...catalog, unavailable: [{ name: site.name, reason: 'duplicate' }] })).toThrow()
    expect(parseCatalog(catalog).sites).toEqual([site])
  })
})

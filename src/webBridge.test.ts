import { describe, expect, it, vi } from 'vitest'
import { HuntWickSession } from './session'
import { createHostedBridge, saveDownload } from './webBridge'

const catalog = { version: 'test', databaseVersion: 'test', updatedAt: '2026-11-24', sites: [
  { name: 'GitHub', url: 'https://github.com/', category: 'Development', quick: true },
  { name: 'GitLab', url: 'https://gitlab.com/', category: 'Development', quick: true },
] }
function fixture() {
  const requests: Array<{ path: string; init?: RequestInit }> = []
  let id = ''
  let controller: ReadableStreamDefaultController<Uint8Array>
  const stream = new ReadableStream<Uint8Array>({ start(c) { controller = c } })
  const get = async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input)
    requests.push({ path, init })
    if (path === '/api/catalog') return Response.json(catalog)
    if (path === '/api/search') {
      id = JSON.parse(String(init?.body)).id
      return new Response(stream, { headers: { 'Content-Type': 'application/x-ndjson' } })
    }
    if (path === '/api/search/' + id + '/cancel') {
      send({ platform: 'GitLab', status: 'cancelled' })
      send({ type: 'done' })
      return new Response(null, { status: 204 })
    }
    throw new Error('Unexpected route')
  }
  function send(fields: Record<string, unknown>) {
    const bytes = new TextEncoder().encode(JSON.stringify({ id, type: 'result', ...fields }) + '\n')
    controller.enqueue(bytes.subarray(0, 9))
    controller.enqueue(bytes.subarray(9))
  }
  return { session: new HuntWickSession(createHostedBridge(get), null), requests, send, close: () => controller.close() }
}

describe('hosted transport', () => {
  it('uses the authenticated catalog and scoped request limits, streams results, and cancels on the server', async () => {
    const { session, requests, send } = fixture()
    await session.connect()
    expect(session.snapshot()).toMatchObject({ hosted: true, desktop: false, ready: true, maxConcurrency: 2, maxTimeout: 20 })
    session.updateSettings({ timeout: 40, concurrency: 10 })
    await session.start('fixture', 'quick')
    const id = session.snapshot().run!.id
    expect(JSON.parse(String(requests[1].init?.body))).toEqual({ id, username: 'fixture', sites: ['GitHub', 'GitLab'], timeout: 20, concurrency: 2 })
    send({ platform: 'GitHub', url: 'https://github.com/fixture', status: 'found' })
    await vi.waitFor(() => expect(session.snapshot().run?.checked).toBe(1))
    await session.cancel()
    expect(requests.map(r => r.path)).toEqual(['/api/catalog', '/api/search', '/api/search/' + id + '/cancel'])
    expect(session.snapshot().run?.results.map(r => r.status)).toEqual(['found', 'cancelled'])
    expect(session.snapshot().run?.phase).toBe('cancelled')
  })
  it('marks a truncated successful HTTP response as a failed search', async () => {
    const { session, close } = fixture()
    await session.connect()
    await session.start('fixture', 'quick')
    close()
    await vi.waitFor(() => expect(session.snapshot().run?.phase).toBe('error'))
    expect(session.snapshot().run?.checked).toBe(0)
  })
  it('aborts the live request and sends a keepalive cancellation when the page exits', async () => {
    const { session, requests } = fixture()
    await session.connect()
    await session.start('fixture', 'quick')
    session.disconnect()
    expect(requests[1].init?.signal?.aborted).toBe(true)
    expect(requests[2].init?.keepalive).toBe(true)
    expect(session.snapshot().run?.phase).toBe('cancelled')
    await session.connect()
    expect(session.snapshot().ready).toBe(true)
  })
  it('displays a rejected API request without inventing any checks', async () => {
    const get = async (input: RequestInfo | URL) => String(input) === '/api/catalog' ? Response.json(catalog) : Response.json({ detail: 'Search capacity reached.' }, { status: 429 })
    const session = new HuntWickSession(createHostedBridge(get), null)
    await session.connect()
    await session.start('fixture', 'quick')
    expect(session.snapshot().run).toMatchObject({ phase: 'error', checked: 0, error: 'Search capacity reached.' })
  })
  it('downloads a report through a local object URL and releases the URL', () => {
    const link = { href: '', download: '', click: vi.fn(), remove: vi.fn() }
    vi.stubGlobal('document', { createElement: () => link, body: { append: vi.fn() } })
    const create = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test')
    const revoke = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    vi.useFakeTimers()
    try {
      saveDownload('csv', 'sample')
      expect(create.mock.calls[0][0]).toMatchObject({ type: 'text/csv;charset=utf-8' })
      expect(link.href).toBe('blob:test')
      expect(link.download).toMatch(/\.csv$/)
      expect(link.click).toHaveBeenCalledOnce()
      vi.runAllTimers()
      expect(revoke).toHaveBeenCalledWith('blob:test')
    } finally { vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals() }
  })
})

import type { ExportFormat } from './model'
import type { Bridge } from './session'

const sizes = { csv: 'text/csv', json: 'application/json', html: 'text/html' }
export function saveDownload(format: ExportFormat, contents: string) {
  const blob = new Blob([contents], { type: sizes[format] + ';charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  try {
    link.href = url
    link.download = 'huntwick-report.' + format
    document.body.append(link)
    link.click()
  } finally {
    link.remove()
    // Give the browser time to begin reading the download.
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
}

interface ActiveSearch {
  id: string
  controller: AbortController
  reading: Promise<void> | null
}

const requestOptions: RequestInit = {
  credentials: 'same-origin', mode: 'same-origin', cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer',
}
const jsonHeaders = { 'Content-Type': 'application/json' }

async function requireOK(response: Response) {
  if (response.ok) return
  const body = await response.json().catch(() => null)
  const fallback = 'The search service returned HTTP ' + response.status + '.'
  throw new Error(typeof body?.detail === 'string' ? body.detail.slice(0, 256) : fallback)
}

/** Decode across byte and line boundaries. A stream must end with a terminal record. */
async function readEvents(response: Response, id: string, emit: (event: unknown) => void) {
  if (!response.body || response.headers.get('content-type')?.split(';')[0].trim() !== 'application/x-ndjson') {
    throw new Error('The search service returned an unexpected response type.')
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8', { fatal: true })
  let pending = ''
  try {
    for (;;) {
      const { value, done } = await reader.read()
      pending += decoder.decode(value, { stream: !done })
      const lines = pending.split('\n')
      pending = done ? '' : lines.pop()!
      for (const line of lines) {
        if (!line.trim()) continue
        if (line.length > 16384) throw new Error('A search result exceeded the size limit.')
        let frame: unknown
        try { frame = JSON.parse(line) } catch { throw new Error('The search service returned a malformed result.') }
        if (!frame || typeof frame !== 'object' || !('id' in frame) || frame.id !== id ||
          !('type' in frame) || !['result', 'done', 'error'].includes(String(frame.type))) {
          throw new Error('The search service returned an invalid event.')
        }
        emit(frame)
        if (frame.type === 'done' || frame.type === 'error') return
      }
      if (pending.length > 16384) throw new Error('A search result exceeded the size limit.')
      if (done) throw new Error('The connection closed before the search finished.')
    }
  } finally {
    void reader.cancel().catch(() => {})
    reader.releaseLock()
  }
}

export function createHostedBridge(fetcher: typeof fetch = fetch): Bridge {
  let listener: ((event: unknown) => void) | undefined
  let active: ActiveSearch | null = null
  let catalogRequest: AbortController | null = null

  function requestCancel(id: string, keepalive: boolean) {
    return fetcher('/api/search/' + encodeURIComponent(id) + '/cancel', {
      ...requestOptions, method: 'POST', headers: jsonHeaders, body: '{}',
      keepalive, signal: AbortSignal.timeout(5000),
    })
  }

  function abandon(task: ActiveSearch) {
    active = null
    task.controller.abort()
    // The server also ends work when the streaming HTTP client disconnects.
    void requestCancel(task.id, true).catch(() => {})
  }

  return {
    desktop: false, hosted: true,
    async catalog() {
      const controller = new AbortController()
      catalogRequest = controller
      const timer = setTimeout(() => controller.abort(), 15000)
      try {
        const response = await fetcher('/api/catalog', { ...requestOptions, signal: controller.signal })
        await requireOK(response)
        return await response.json()
      } finally {
        clearTimeout(timer)
        if (catalogRequest === controller) catalogRequest = null
      }
    },
    async listen(notify) {
      listener = notify
      return () => { if (listener === notify) listener = undefined }
    },
    async start(request) {
      if (active) throw new Error('A hosted search is already running.')
      const task: ActiveSearch = { id: request.id, controller: new AbortController(), reading: null }
      active = task
      // The hosted catalog is limited to two sites and twenty seconds per check.
      const deadline = setTimeout(() => task.controller.abort(), 60000)
      try {
        const response = await fetcher('/api/search', {
          ...requestOptions, method: 'POST', headers: { ...jsonHeaders, Accept: 'application/x-ndjson' },
          body: JSON.stringify(request), signal: task.controller.signal,
        })
        await requireOK(response)
        if (active !== task) { void response.body?.cancel().catch(() => {}); return }
        task.reading = readEvents(response, request.id, frame => {
          if (active === task) listener?.(frame)
        }).catch(error => {
          if (active === task) listener?.({ type: 'error', id: request.id,
            message: task.controller.signal.aborted ? 'The search connection timed out.' :
              error instanceof Error ? error.message : 'The search connection failed.' })
        }).finally(() => {
          clearTimeout(deadline)
          if (active === task) active = null
          task.controller.abort()
        })
      } catch (error) {
        if (active !== task) return
        active = null
        if (task.controller.signal.aborted) throw new Error('The search connection timed out.')
        throw error
      } finally {
        if (!task.reading) clearTimeout(deadline)
      }
    },
    async cancel(id) {
      const task = active
      if (!task || task.id !== id) return
      if (!task.reading) { abandon(task); return }
      const response = await requestCancel(id, false)
      if (response.status !== 404) await requireOK(response)
      // The acknowledgment can arrive before results already produced by the server.
      // Let the stream deliver these rows and its terminal record.
      let timer: ReturnType<typeof setTimeout> | undefined
      try {
        await Promise.race([task.reading, new Promise<void>(resolve => { timer = setTimeout(resolve, 5000) })])
      } finally {
        clearTimeout(timer)
        if (active === task) { active = null; task.controller.abort() }
      }
    },
    close() {
      catalogRequest?.abort()
      if (active) abandon(active)
    },
    async open(url) { window.open(url, '_blank', 'noopener,noreferrer') },
    async save(format, contents) { saveDownload(format, contents); return true },
  }
}

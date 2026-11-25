/// <reference types="vite/client" />
import { useEffect, useState, useSyncExternalStore } from 'react'
import { invoke, isTauri } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { HuntWickSession } from './session'
import { createHostedBridge } from './webBridge'
import type { Bridge, LocalStore } from './session'

function createSession() {
  let store: LocalStore | null = null
  try { store = window.localStorage } catch { /* Storage may be disabled in the host. */ }
  const desktop = isTauri()
  if (!desktop && import.meta.env.VITE_HUNTWICK_WEB === '1') return new HuntWickSession(createHostedBridge(), store)
  const bridge: Bridge = {
    desktop,
    catalog: async (policy) => {
      if (desktop) return invoke('catalog', policy)
      const response = await fetch('./catalog.json', { credentials: 'same-origin' })
      if (!response.ok) throw new Error('The bundled preview catalog could not be loaded.')
      return response.json()
    },
    listen: fn => listen<unknown>('engine-event', event => fn(event.payload)),
    start: request => invoke('start_search', { request }),
    cancel: id => invoke('cancel_search', { id }),
    open: async url => {
      if (desktop) return invoke('open_url', { url })
      window.open(url, '_blank', 'noopener,noreferrer')
    },
    save: (format, contents) => {
      if (!desktop) return Promise.reject(new Error('Open the desktop app to export results.'))
      return invoke('save_export', { format, contents })
    },
  }
  return new HuntWickSession(bridge, store)
}

export function useHuntWick() {
  const [session] = useState(createSession)
  const state = useSyncExternalStore(session.subscribe, session.snapshot)
  useEffect(() => {
    void session.connect()
    const restore = (event: PageTransitionEvent) => { if (event.persisted) void session.connect() }
    if (session.snapshot().hosted) {
      window.addEventListener('pagehide', session.disconnect)
      window.addEventListener('pageshow', restore)
    }
    return () => {
      window.removeEventListener('pagehide', session.disconnect)
      window.removeEventListener('pageshow', restore)
      session.disconnect()
    }
  }, [session])
  useEffect(() => {
    if (!state.desktop || !state.ready || !state.catalog || !('__HUNTWICK_VERIFY_INSTALL__' in window)) return
    const siteCount = state.catalog.sites.length
    const frame = requestAnimationFrame(() => {
      const input = document.querySelector<HTMLInputElement>('main form input#username')
      if (input?.offsetWidth && input.offsetHeight && input.form?.querySelector('button[type="submit"]')) {
        void invoke('confirm_install', { siteCount })
      }
    })
    return () => cancelAnimationFrame(frame)
  }, [state.ready, state.catalog])
  return {
    ...state,
    start: session.start, cancel: session.cancel, clearRun: session.clearRun,
    clearError: session.clearError, retryCatalog: session.connect, updateSettings: session.updateSettings,
    loadHistory: session.loadHistory, deleteHistory: session.deleteHistory, clearHistory: session.clearHistory,
    clearLocalData: session.clearLocalData,
    openUrl: session.openUrl, exportRun: session.exportRun,
  }
}

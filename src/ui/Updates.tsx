import { useEffect, useRef, useState } from 'react'
import { ArrowDownToLine, CircleAlert, CircleCheck, ExternalLink, RefreshCw } from 'lucide-react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { desktopDownloadsUrl, isActive, Toggle, version, type Workspace } from './common'
import { ReleaseNotes } from './ReleaseNotes'
import './updates.css'

type Offer = {version: string; notes: string}
type Phase = 'idle' | 'checking' | 'current' | 'available' | 'confirm' | 'downloading' | 'error'
type Transfer = [number, number | null]

function size(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 ** 2) return (bytes / 1024).toFixed(1) + ' KiB'
  return (bytes / 1024 ** 2).toFixed(1) + ' MiB'
}

export function Updates({ws, visible}: {ws: Workspace; visible: boolean}) {
  const { autoUpdates, includePrereleases } = ws.settings
  const [phase, setPhase] = useState<Phase>('idle')
  const [offer, setOffer] = useState<Offer | null>(null)
  const [error, setError] = useState('')
  const [transfer, setTransfer] = useState<Transfer>([0, null])
  const startup = useRef(true)
  const busy = phase === 'checking' || phase === 'downloading'
  const active = isActive(ws.run)
  async function check(prerelease: boolean) {
    setPhase('checking')
    setOffer(null)
    try {
      const found = await invoke<Offer | null>('check_update', {prerelease})
      setOffer(found)
      setPhase(found ? 'available' : 'current')
    } catch (e) {
      setError(String(e))
      setPhase('error')
    }
  }
  useEffect(() => {
    if (!startup.current) return
    startup.current = false
    if (autoUpdates) void check(includePrereleases)
  }, [autoUpdates, includePrereleases])

  async function install() {
    if (!offer || active || phase !== 'confirm') return
    setTransfer([0, null])
    setPhase('downloading')
    let unlisten: (() => void) | undefined
    try {
      unlisten = await listen<Transfer>('update-progress', ({payload}) => setTransfer(payload))
      await invoke('install_update', {version: offer.version})
    } catch (e) {
      setError(String(e))
      setOffer(null)
      setPhase('error')
    } finally { unlisten?.() }
  }

  if (!visible) return offer ? <p role="status">HuntWick {offer.version} is available in Settings.</p> : null
  const [downloaded, total] = transfer
  const percent = total && total > 0 ? Math.min(100, Math.floor(100 * downloaded / total)) : undefined
  return <section className="settings-panel updates-panel" aria-label="Software updates">
    <h2><RefreshCw size={17}/>Software updates <small>Installed {version}</small></h2>
    <div className="preference"><div><strong>Automatic update checks</strong>
      <small>Check for {includePrereleases ? 'stable releases and prereleases' : 'stable releases'} at startup.</small></div>
      <Toggle label="Automatic update checks" checked={autoUpdates} onChange={() => ws.updateSettings({autoUpdates: !autoUpdates})}/></div>
    <div className="preference"><div><strong>Include prereleases</strong>
      <small>Include preview versions in manual and automatic checks.</small></div>
      <Toggle label="Include prereleases" checked={includePrereleases} disabled={busy} onChange={() => {
        ws.updateSettings({includePrereleases: !includePrereleases})
        setOffer(null)
        setPhase('idle')
      }}/></div>
    <div className="update-body">
      <div className="update-actions">
        <button className="primary" disabled={busy} onClick={() => void check(includePrereleases)}>Check for updates</button>
        <button className="text-action" onClick={() => void ws.openUrl(desktopDownloadsUrl)}>Manual downloads <ExternalLink size={13}/></button>
      </div>
      {phase === 'checking' && <p role="status">Checking release feeds…</p>}
      {phase === 'current' && <div className="update-notice" role="status"><CircleCheck size={17}/> No newer update is available.</div>}
      {phase === 'error' && <div className="update-notice update-error" role="alert"><CircleAlert size={17}/><div><strong>Update failed</strong><p>{error}</p></div></div>}
      {offer && <article className="update-card">
        <header><ArrowDownToLine size={20}/><div><h3>Update available</h3><p>HuntWick {offer.version}</p></div></header>
        <div className="update-notes"><h4>Release notes</h4><ReleaseNotes notes={offer.notes}/></div>
        <footer>
          {phase === 'downloading' ? <div className="update-transfer">
            <strong>Downloading signed update</strong>
            <progress aria-label="Download progress" max={100} value={percent}/>
            <span>{percent === undefined ? size(downloaded) + ' downloaded' : percent + '% · ' + size(downloaded) + ' of ' + size(total!)}</span>
          </div> : <>
            {active && <p>Finish or cancel the active search to install this update.</p>}
            {phase === 'confirm' ? <>
              <strong>Restart to install HuntWick {offer.version}?</strong>
              <p>HuntWick will download and verify the update, then close and restart.</p>
              <div className="update-actions">
                <button className="primary" disabled={active} onClick={() => void install()}>Confirm restart</button>
                <button className="quiet small" onClick={() => setPhase('available')}>Cancel</button>
              </div>
            </> : <button className="primary" disabled={active} onClick={() => setPhase('confirm')}>Install {offer.version} and restart</button>}
          </>}
        </footer>
      </article>}
    </div>
  </section>
}

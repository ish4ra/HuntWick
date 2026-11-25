import { useEffect, useState, useRef } from 'react'
import { RefreshCw, ExternalLink } from 'lucide-react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { desktopDownloadsUrl, isActive, Toggle, version, type Workspace } from './common'

type Offer = {version:string; notes:string}

export function Updates({ws, visible}: {ws:Workspace;visible:boolean}) {
  const [offer,setOffer] = useState<Offer|null>(null)
  const [status,setStatus] = useState('')
  const [busy,setBusy] = useState(false)
  const [confirm,setConfirm] = useState(false)
  const [progress,setProgress] = useState<number|null>(null)
  const checked = useRef(false)
  async function check(prerelease:boolean) {
    setBusy(true); setConfirm(false); setOffer(null); setStatus('Checking release feed…')
    try {
      const found = await invoke<Offer|null>('check_update',{prerelease})
      setOffer(found); setStatus(found ? 'Available update: '+found.version : 'No newer update is available.')
    } catch (e) { setStatus(String(e)) } finally { setBusy(false) }
  }
  useEffect(() => {
    if (ws.settings.autoUpdates && !checked.current) { checked.current=true; void check(false) }
  },[ws.settings.autoUpdates])
  async function install() {
    if (!offer || isActive(ws.run)) return
    setBusy(true); setConfirm(false); setStatus('Downloading signed update…')
    let unlisten: (()=>void)|undefined
    try {
      unlisten = await listen<[number,number|null]>('update-progress',({payload:[bytes,total]}) =>{
        const pct=total ? Math.min(100,Math.floor(100*bytes/total)) : null
        setProgress(pct);setStatus(pct!==null ? pct+'% downloaded' : Math.ceil(bytes/1024)+' KiB downloaded')
      })
      await invoke('install_update',{version:offer.version})
    } catch(e) { setStatus(String(e)); setOffer(null) } finally {unlisten?.();setProgress(null);setBusy(false)}
  }
  if (!visible) return offer ? <p role="status">HuntWick {offer.version} is available in Settings.</p> : null
  return <section className="settings-panel" aria-label="Software updates">
    <h2><RefreshCw size={17}/>Software updates</h2>
    <div className="preference"><div><strong>Automatic update checks</strong><small>Check the stable channel at startup. Installed version {version}.</small></div>
      <Toggle label="Automatic update checks" checked={ws.settings.autoUpdates} onChange={()=>ws.updateSettings({autoUpdates:!ws.settings.autoUpdates})}/></div>
    <div className="update-body"><div className="update-actions">
      <button className="primary" disabled={busy} onClick={()=>void check(false)}>Check for updates</button>
      <button className="quiet small" disabled={busy} onClick={()=>void check(true)}>Check prereleases</button>
      <button className="text-action" onClick={()=>void ws.openUrl(desktopDownloadsUrl)}>Manual downloads <ExternalLink size={13}/></button>
    </div><p role="status">{status}</p>
    {progress!==null && <progress aria-label="Download progress" max={100} value={progress}/>}
    {offer && <><h3>Release notes</h3><p>{offer.notes || 'No notes supplied.'}</p>
      {confirm ? <div className="update-actions"><span>HuntWick will close, install the signed update and restart.</span>
        <button className="primary" disabled={busy || isActive(ws.run)} onClick={()=>void install()}>Confirm restart</button>
        <button className="quiet small" onClick={()=>setConfirm(false)}>Cancel</button></div> :
        <button className="primary" disabled={busy || isActive(ws.run)} onClick={()=>setConfirm(true)}>Install {offer.version} and restart</button>}</>}
    </div></section>
}

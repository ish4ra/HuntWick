import {useEffect, useState, useRef} from 'react'
import {invoke} from '@tauri-apps/api/core'
import {listen} from '@tauri-apps/api/event'
import {isActive, version, type Workspace} from './common'

type Offer = {version:string; notes:string}

export function Updates({ws, visible}: {ws:Workspace;visible:boolean}) {
  const [offer,setOffer] = useState<Offer|null>(null)
  const [status,setStatus] = useState('')
  const [busy,setBusy] = useState(false)
  const checked = useRef(false)
  async function check(prerelease:boolean) {
    setBusy(true); setOffer(null); setStatus('Checking release feed…')
    try {
      const found = await invoke<Offer|null>('check_update',{prerelease})
      setOffer(found); setStatus(found ? 'Available update: '+found.version : 'Up to date.')
    } catch (e) { setStatus(String(e)) } finally { setBusy(false) }
  }
  useEffect(() => {
    if (ws.settings.autoUpdates && !checked.current) { checked.current=true; void check(false) }
  },[ws.settings.autoUpdates])
  async function install() {
    if (!offer) return
    setBusy(true)
    let unlisten: (()=>void)|undefined
    try {
      unlisten = await listen<[number,number|null]>('update-progress',({payload:[bytes,total]}) =>
        setStatus(total ? Math.floor(100*bytes/total)+'% downloaded' : Math.ceil(bytes/1024)+' KiB downloaded'))
      await invoke('install_update',{version:offer.version})
    } catch(e) { setStatus(String(e)); setOffer(null) } finally {unlisten?.();setBusy(false)}
  }
  if (!visible) return offer ? <p role="status">HuntWick {offer.version} is available in Settings.</p> : null
  return <section className="settings-panel"><h2>Software updates</h2><p>Installed version {version}</p>
    <label><input type="checkbox" checked={ws.settings.autoUpdates} onChange={e=>ws.updateSettings({autoUpdates:e.target.checked})}/>Check for stable updates at startup</label>
    <div className="actions"><button disabled={busy} onClick={()=>void check(false)}>Check stable</button>
    <button disabled={busy} onClick={()=>void check(true)}>Check prereleases</button>
    <button onClick={()=>void ws.openUrl('https://github.com/ish4ra/HuntWick/releases')}>Manual downloads</button></div>
    <p role="status">{status}</p>{offer && <><p>{offer.notes}</p><button disabled={busy || isActive(ws.run)} onClick={()=>void install()}>Install {offer.version} and restart</button></>}
  </section>
}

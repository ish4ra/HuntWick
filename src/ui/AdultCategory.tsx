import { useState } from 'react'
import { Toggle, type Workspace } from './common'

export function AdultCategory({ws}: {ws: Workspace}) {
  const [confirm, setConfirm] = useState(false)
  const {includeNsfw, adultConsent} = ws.settings
  return <div className="adult-category"><label>Include NSFW platforms</label>
    <Toggle label="Include NSFW platforms" checked={includeNsfw} onChange={() => {
      if (includeNsfw || adultConsent) ws.updateSettings({includeNsfw: !includeNsfw})
      else setConfirm(true)
    }}/>
    {confirm && <div role="group" aria-label="Adult category consent">
      Include adult-labeled public profiles in future searches?
      <button type="button" onClick={()=>{ws.updateSettings({includeNsfw:true,adultConsent:true});setConfirm(false)}}>Confirm inclusion</button>
      <button type="button" onClick={()=>setConfirm(false)}>Cancel</button>
    </div>}
  </div>
}

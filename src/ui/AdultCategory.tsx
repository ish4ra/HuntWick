import { Toggle, type Workspace } from './common'

export function AdultCategory({ws}: {ws: Workspace}) {
  const {includeNsfw} = ws.settings
  return <div className="adult-category">
    <div><strong>Include NSFW platforms</strong>
      <small>{includeNsfw ? 'Included in eligible searches' : 'Excluded from searches'}</small></div>
    <Toggle label="Include NSFW platforms" checked={includeNsfw} onChange={()=>
      ws.updateSettings({includeNsfw:!includeNsfw, adultConsent:true})}/>
  </div>
}

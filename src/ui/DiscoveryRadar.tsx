import {useState} from 'react'
import {PlatformMark, isActive, statuses, type Workspace} from './common'

export function DiscoveryRadar({ws}:{ws:Workspace}) {
  const rows=ws.run?.results.filter(r=>r.status==='found'||r.status==='possible') ?? []
  const active=isActive(ws.run)
  const [selected,setSelected]=useState('')
  const detail=rows.find(r=>r.platform===selected)
  return <section className={'scope-radar'+(active?' scanning':'')} aria-label="Profile discoveries">
    <div className="radar-grid"/><div className="radar-axis-x"/><div className="radar-axis-y"/>
    <div className="radar-disc"><div className="sweep"/>
      {rows.map((r,i)=>{
        const radius=12+30*((i*.61803398875)%1), angle=i*2.39996
        const label=r.platform+' · '+statuses[r.status]
        return <button type="button" key={r.platform} className={'discovery-dot '+r.status}
          style={{left:(50+radius*Math.cos(angle))+'%',top:(50+radius*Math.sin(angle))+'%'}}
          title={label} aria-label={label} onFocus={()=>setSelected(r.platform)} onMouseEnter={()=>setSelected(r.platform)}
          onClick={()=>setSelected(r.platform)}/>
      })}
    </div>
    {detail && <div className="radar-detail"><PlatformMark name={detail.platform}/><button type="button" onClick={()=>void ws.openUrl(detail.url)}>{detail.platform} · {statuses[detail.status]}</button></div>}
  </section>
}

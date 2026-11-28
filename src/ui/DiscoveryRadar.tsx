import {isActive, statuses, type Workspace} from './common'

export function DiscoveryRadar({ws}:{ws:Workspace}) {
  const rows=ws.run?.results.filter(r=>['found','possible','provider_match','conflict'].includes(r.status)) ?? []
  const active=isActive(ws.run)
  return <section className={'scope-radar'+(active?' scanning':'')} aria-label="Profile discoveries">
    <div className="radar-grid"/><div className="radar-axis-x"/><div className="radar-axis-y"/>
    <div className="radar-disc"><div className="sweep"/>
      {rows.map((r,i)=>{
        const radius=12+30*((i*.61803398875)%1), angle=i*2.39996
        const label=r.platform+' · '+statuses[r.status]
        return <button type="button" key={r.platform} className={'discovery-dot '+r.status}
          style={{left:(50+radius*Math.cos(angle))+'%',top:(50+radius*Math.sin(angle))+'%'}}
          title={label} aria-label={label} onClick={()=>void ws.openUrl(r.url)}><span className="radar-blip" aria-hidden="true"/></button>
      })}
    </div>
  </section>
}

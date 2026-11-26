import {invoke} from '@tauri-apps/api/core'
import {listen} from '@tauri-apps/api/event'

export async function driveUpgrade(siteCount: number) {
  const report=(step:string)=>invoke('confirm_install',{siteCount,step})
  const check=(prerelease:boolean)=>invoke<{version:string}|null>('check_update',{prerelease})
  const mustReject=async(p:Promise<unknown>)=>{
    try {await p} catch {return}
    throw Error('Expected update operation to fail')
  }
  await invoke('confirm_install',{siteCount})
  localStorage.setItem('huntwick.preferences.v1', JSON.stringify({saveHistory:true,theme:'light',autoUpdates:false}))
  const timestamp='2026-01-01T00:00:00Z'
  const history=[{id:'fixture-preservation',username:'fixture',startedAt:timestamp,finishedAt:timestamp,
    mode:'quick',phase:'complete',error:null,checked:1,sites:['Fixture'],results:[{
      platform:'Fixture',category:'Other',status:'not_found',message:'',url:''}]}]
  localStorage.setItem('huntwick.history.v1', JSON.stringify(history))
  await report('missing manifest')
  await mustReject(check(false))
  await report('stable isolation')
  if (await check(false)) throw Error('Stable check accepted a prerelease')
  await report('downgrade')
  if (await check(true)) throw Error('Downgrade accepted')
  await report('unsupported platform')
  await mustReject(check(true))
  let received=0
  const stop=await listen<[number,number|null]>('update-progress',({payload:[bytes]})=>{received=bytes})
  await report('invalid signature')
  const damaged=await check(true)
  if (!damaged) throw Error('Missing signature fixture')
  await mustReject(invoke('install_update',{version:damaged.version}))
  stop()
  if (received<=0) throw Error('No download progress from the installed updater')
  await report('stable supersedes older preview')
  if ((await check(true))?.version !== '1.10.0') throw Error('Older preview superseded stable update')
  await report('signed candidate')
  const valid=await check(true)
  if (!valid) throw Error('Missing valid update')
  await invoke('install_update',{version:valid.version})
}

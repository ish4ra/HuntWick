import {invoke} from '@tauri-apps/api/core'
import {listen} from '@tauri-apps/api/event'

export async function driveUpgrade(siteCount: number) {
  const report=(step:string)=>invoke('confirm_install',{siteCount,step})
  type CheckResult = {offer: {version:string}|null; previewVersion:string|null; feedMessage:string|null}
  const check=(prerelease:boolean, discoverPreview=false)=>invoke<CheckResult>('check_update',{prerelease,discoverPreview})
  const mustReject=async(p:Promise<unknown>)=>{
    try {await p} catch {return}
    throw Error('Expected update operation to fail')
  }
  await invoke('confirm_install',{siteCount})
  localStorage.setItem('huntwick.preferences.v1', JSON.stringify({saveHistory:true,includePrereleases:true,theme:'light',autoUpdates:false}))
  const timestamp='2026-01-01T00:00:00Z'
  const history=[{id:'fixture-preservation',username:'fixture',startedAt:timestamp,finishedAt:timestamp,
    mode:'quick',phase:'complete',error:null,checked:1,sites:['Fixture'],results:[{
      platform:'Fixture',category:'Other',status:'not_found',message:'',url:''}]}]
  localStorage.setItem('huntwick.history.v1', JSON.stringify(history))
  await report('missing manifest')
  const unpublished=await check(false)
  if (unpublished.offer || !unpublished.feedMessage?.includes('No update feed has been published'))
    throw Error('Missing feed was not identified')
  await report('stable isolation')
  const notice=await check(false,true)
  if (notice.offer || !notice.previewVersion) throw Error('Expected an informational preview notice')
  await mustReject(invoke('install_update',{version:notice.previewVersion}))
  await report('downgrade')
  const downgrade=await check(true)
  if (downgrade.offer || downgrade.previewVersion || downgrade.feedMessage) throw Error('Expected both channels current')
  await report('unsupported platform')
  const unsupported=await check(true)
  if (unsupported.offer || !unsupported.feedMessage?.includes('does not support this platform'))
    throw Error('Expected unsupported release metadata')
  let received=0
  const stop=await listen<[number,number|null]>('update-progress',({payload:[bytes]})=>{received=bytes})
  await report('invalid signature')
  const {offer:damaged}=await check(true)
  if (!damaged) throw Error('Missing signature fixture')
  await mustReject(invoke('install_update',{version:damaged.version}))
  stop()
  if (received<=0) throw Error('No download progress from the installed updater')
  await report('stable supersedes older preview')
  if ((await check(true)).offer?.version !== '1.10.0') throw Error('Older preview superseded stable update')
  await report('signed candidate')
  const {offer:valid}=await check(true)
  if (!valid) throw Error('Missing valid update')
  await invoke('install_update',{version:valid.version})
}

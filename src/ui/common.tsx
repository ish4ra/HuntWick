import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Check, Copy, Globe2, LoaderCircle } from 'lucide-react'
import { useHuntWick } from '../useHuntWick'
import { activeRun, type Run } from '../model'
export { statusLabels as statuses } from '../model'

export type Workspace = ReturnType<typeof useHuntWick>
export type Page = 'Search' | 'History' | 'Platforms' | 'Settings' | 'About'
export const repositoryUrl = 'https://github.com/ish4ra/HuntWick'
export const desktopDownloadsUrl = repositoryUrl + '/releases/tag/v0.1.0-rc.5'
export const webPrivacy =
  'The service operator receives your IP address and the username you submit. Selected platforms receive the username and the server’s IP address.'
export const version = '0.1.0-rc.6'
export const phases: Record<Run['phase'], string> = {
  running: 'Running',
  cancelling: 'Cancelling',
  cancelled: 'Cancelled',
  complete: 'Complete',
  error: 'Failed',
}
export const isActive = activeRun
export function duration(start: string, end: string | number) {
  const seconds = Math.max(0, Math.floor((new Date(end).getTime() - Date.parse(start)) / 1000))
  return `${Math.floor(seconds / 60)
    .toString()
    .padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`
}
export function useElapsed(run: Run | null) {
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    if (!isActive(run)) return
    setNow(Date.now())
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [run?.id, run?.phase])
  const end = run?.finishedAt ? Date.parse(run.finishedAt) : now
  return {elapsed: run ? duration(run.startedAt, end) : '00:00', seconds: run ? Math.max(0,(end-Date.parse(run.startedAt))/1000) : 0}
}
async function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return
    } catch {
      /* Try the WebView selection API. */
    }
  }
  const previous = document.activeElement
  const field = document.createElement('textarea')
  field.value = text
  field.className = 'sr-only'
  document.body.append(field)
  try {
    field.select()
    if (!document.execCommand('copy')) throw new Error('Clipboard unavailable')
  } finally {
    field.remove()
    if (previous instanceof HTMLElement) previous.focus()
  }
}
export function CopyLink({ url, action }: { url: string; action?: string }) {
  const [status, setStatus] = useState<'idle' | 'copied' | 'error'>('idle')
  const timer = useRef<number | undefined>(undefined)
  useEffect(() => () => window.clearTimeout(timer.current), [])
  async function copy() {
    try {
      await copyText(url)
      setStatus('copied')
    } catch {
      setStatus('error')
    }
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => setStatus('idle'), 2200)
  }
  const label = action ?? 'Copy profile link'
  return (
    <span className="copy-wrap">
      <button
        className={action ? 'quiet small' : 'icon-button'}
        title={label}
        aria-label={label}
        disabled={!url}
        onClick={copy}
      >
        {status === 'copied' ? <Check size={15} /> : <Copy size={15} />}
        {action && <span>{action}</span>}
      </button>
      {status !== 'idle' && (
        <span className="copy-feedback" role="status">
          {status === 'copied' ? 'Copied' : 'Copy failed'}
        </span>
      )}
    </span>
  )
}
const platformIcons: Record<string,string> = {'kofi':'kofi','Ko-fi':'kofi','MyAnimeList':'myanimelist','Patreon':'patreon','VirusTotal':'virustotal','Scratch':'scratch','Replit.com':'replit','RubyGems':'rubygems','Letterboxd':'letterboxd','Chess.com':'chessdotcom','osu!':'osu','GitHub':'github','GitLab':'gitlab','Docker Hub':'docker','Codeberg':'codeberg','Twitch':'twitch','Instagram':'instagram','Reddit':'reddit','X (Twitter)':'x','YouTube':'youtube','TikTok':'tiktok','Hugging Face':'huggingface','Lichess':'lichess','Bluesky':'bluesky','Trello':'trello','Codewars':'codewars'}
export function PlatformMark({ name }: { name: string }) {
  const icon = platformIcons[name]
  if (icon) return <span className="brand-mark" aria-hidden="true" style={{maskImage:`url(/platforms/${icon}.svg)`}}/>
  const hash = Array.from(name).reduce((value, c) => (value * 31 + c.charCodeAt(0)) >>> 0, 0)
  return (
    <span aria-hidden="true" className={'platform-mark hue-' + (hash % 4)}>
      <Globe2 size={16}/>
    </span>
  )
}
export function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean
  onChange: () => void
  label: string
}) {
  return (
    <button
      className="toggle"
      type="button"
      role="switch"
      aria-label={label}
      aria-checked={checked}
      onClick={onChange}
    >
      <span />
    </button>
  )
}
export function Empty({ icon, title, children }: { icon: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="empty">
      <span className="empty-icon">{icon}</span>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
    </div>
  )
}
export function Busy() {
  return <LoaderCircle size={15} className="spin" aria-hidden="true" />
}
export function dateTime(value: string) {
  return new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

import { useState, type ReactNode } from 'react'
import {
  BookOpen,
  Database,
  ExternalLink,
  Github,
  Info,
  LockKeyhole,
  Monitor,
  Palette,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import type { Mode, Settings } from '../model'
import { Intro } from './LibraryPages'
import { NumberSetting } from './SearchPage'
import {
  desktopDownloadsUrl,
  isActive,
  repositoryUrl,
  Toggle,
  version,
  webPrivacy,
  type Workspace,
} from './common'

function Panel({ title, icon, children }: { title: string; icon: ReactNode; children: ReactNode }) {
  return (
    <section className="settings-panel">
      <h2>
        {icon}
        {title}
      </h2>
      {children}
    </section>
  )
}
function Preference({ title, hint, children }: { title: string; hint: string; children: ReactNode }) {
  return (
    <div className="preference">
      <div>
        <strong>{title}</strong>
        <small>{hint}</small>
      </div>
      {children}
    </div>
  )
}
export function SettingsPage({ ws }: { ws: Workspace }) {
  const s = ws.settings
  const [confirmAdult, setConfirmAdult] = useState(false)
  const [confirmClear, setConfirmClear] = useState(false)
  return (
    <>
      <Intro
        label="PREFERENCES"
        title="Settings"
        description="Manage your workspace appearance, search defaults and local history."
      />
      <Panel title="Discovery radar" icon={<Monitor size={17}/>}>
        <Preference title="Detection sound" hint="One short ping for new matches. Closely spaced detections share a ping.">
          <Toggle label="Detection sound" checked={s.radarSound} onChange={()=>ws.updateSettings({radarSound:!s.radarSound})}/>
        </Preference><Preference title="Volume" hint="Applies to detection sounds.">
          <input type="range" aria-label="Radar volume" min="0" max="100" value={s.radarVolume} onChange={e=>ws.updateSettings({radarVolume:Number(e.target.value)})}/>
        </Preference>
      </Panel>
      <Panel title="Appearance" icon={<Palette size={17} />}>
        <Preference title="Color theme" hint="Use your device theme or choose a workspace theme.">
          <select
            aria-label="Color theme"
            value={s.theme}
            onChange={(e) => ws.updateSettings({ theme: e.target.value as Settings['theme'] })}
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="system">System</option>
          </select>
        </Preference>
        <Preference title="Display density" hint="Set the spacing of result rows and cards.">
          <select
            aria-label="Display density"
            value={s.density}
            onChange={(e) => ws.updateSettings({ density: e.target.value as Settings['density'] })}
          >
            <option value="comfortable">Comfortable</option>
            <option value="compact">Compact</option>
          </select>
        </Preference>
      </Panel>
      {ws.desktop && <Panel title="Desktop catalog" icon={<Database size={17} />}>
        <fieldset disabled={isActive(ws.run)}><Preference title="Include adult platforms" hint="Public profile checks only. A matching name does not establish identity or interests.">
          <button onClick={() => s.includeNsfw ? ws.updateSettings({includeNsfw:false}) : setConfirmAdult(true)}>{s.includeNsfw ? 'Disable adult platforms' : 'Include NSFW platforms…'}</button>
          {confirmAdult && <div role="group" aria-label="Confirm adult platforms">Include adult-labeled sites in the directory and Full Search?
          <button onClick={() => {ws.updateSettings({includeNsfw:true});setConfirmAdult(false)}}>Confirm inclusion</button>
          <button onClick={() => setConfirmAdult(false)}>Cancel</button></div>}
        </Preference><Preference title="Include upstream-excluded sites" hint="Experimental checks can return false positives. Their strongest result is Possible Match.">
          <Toggle checked={s.includeExcluded} label="Include upstream-excluded sites" onChange={() => ws.updateSettings({includeExcluded:!s.includeExcluded})}/>
        </Preference></fieldset>
      </Panel>}
      <Panel title="Search defaults" icon={<SlidersHorizontal size={17} />}>
        <Preference
          title="Remember search preferences"
          hint={
            ws.hosted
              ? 'Save check timeouts and concurrency in this browser.'
              : 'Keep your search limits and default mode between app sessions.'
          }
        >
          <Toggle
            checked={s.rememberPreferences}
            label="Remember search preferences"
            onChange={() => ws.updateSettings({ rememberPreferences: !s.rememberPreferences })}
          />
        </Preference>
        {!ws.hosted && (
          <Preference title="Default search mode" hint="Choose the mode selected when you open a new search.">
            <select
              aria-label="Default search mode"
              value={s.defaultMode}
              onChange={(e) => ws.updateSettings({ defaultMode: e.target.value as Mode })}
            >
              <option value="quick">Quick search</option>
              <option value="full">Full search</option>
            </select>
          </Preference>
        )}
        <div className="pref-numbers">
          <NumberSetting
            label="Timeout per platform (seconds)"
            value={s.timeout}
            min={1}
            max={ws.maxTimeout}
            onChange={(timeout) => ws.updateSettings({ timeout })}
          />
          <NumberSetting
            label="Concurrent platform checks"
            value={s.concurrency}
            min={1}
            max={ws.maxConcurrency}
            onChange={(concurrency) => ws.updateSettings({ concurrency })}
          />
        </div>
      </Panel>
      <Panel title="Privacy" icon={<LockKeyhole size={17} />}>
        <Preference
          title="Save search history"
          hint={
            ws.hosted
              ? 'Store completed searches in this browser for later review.'
              : 'Store completed searches on this device for later review.'
          }
        >
          <Toggle
            checked={s.saveHistory}
            label="Save search history"
            onChange={() => ws.updateSettings({ saveHistory: !s.saveHistory })}
          />
        </Preference>
        <p className="settings-note">
          {ws.hosted
            ? webPrivacy
            : 'Search requests go directly to the selected platforms, which can see your IP address and the username you check.'}
        </p>
        <Preference
          title="Clear local application data"
          hint={
            ws.hosted
              ? 'Remove saved searches and preferences from this browser.'
              : 'Remove saved searches and preferences from this device.'
          }
        >
          <button className="danger small" disabled={isActive(ws.run)} onClick={() => setConfirmClear(true)}>
            Clear local data
          </button>
        </Preference>
        {confirmClear && (
          <div className="clear-confirm" role="alert">
            <p>Delete all local search history and restore default settings?</p>
            <div className="actions">
              <button className="quiet small" onClick={() => setConfirmClear(false)}>
                Keep data
              </button>
              <button
                className="danger small"
                disabled={isActive(ws.run)}
                onClick={() => {
                  if (ws.clearLocalData()) setConfirmClear(false)
                }}
              >
                Delete local data
              </button>
            </div>
          </div>
        )}
      </Panel>
    </>
  )
}
export function AboutPage({ ws }: { ws: Workspace }) {
  return (
    <>
      <Intro
        label="APPLICATION"
        title="About HuntWick"
        description={
          ws.hosted
            ? 'An open-source web workspace for authorized public profile checks.'
            : 'An open-source desktop workspace for public profile discovery.'
        }
      />
      <section className="about-brand">
        <img src="/huntwick.svg" alt="" />
        <div>
          <h2><span className="wordmark" role="img" aria-label="HuntWick" />{ws.hosted && ' Web'}</h2>
          <p>OSINT, simplified.</p>
          <span className="version-tag">v{version}</span>
        </div>
      </section>
      <Panel title="Workspace details" icon={<Info size={17} />}>
        <div className="about-row">
          <Monitor size={16} />
          <span>Application version</span>
          <strong>{version}</strong>
        </div>
        <div className="about-row">
          <Database size={16} />
          <span>Platform database</span>
          <strong>{ws.catalog?.databaseVersion ?? 'Unavailable'}</strong>
        </div>
        <div className="about-row">
          <Database size={16} />
          <span>Platforms in catalog</span>
          <strong>{ws.catalog?.sites.length ?? 'Unavailable'}</strong>
        </div>
        <div className="about-row">
          <BookOpen size={16} />
          <span>License</span>
          <strong>MIT</strong>
        </div>
        {ws.hosted && (
          <div className="about-row">
            <Monitor size={16} />
            <span>Desktop installers</span>
            <a href={desktopDownloadsUrl} target="_blank" rel="noreferrer" className="text-action">
              View release candidate build <ExternalLink size={13} />
            </a>
          </div>
        )}
        <div className="about-row">
          <Github size={16} />
          <span>Source repository</span>
          <button className="text-action" onClick={() => void ws.openUrl(repositoryUrl)}>
            ish4ra/HuntWick <ExternalLink size={13} />
          </button>
        </div>
      </Panel>
      <Panel title="Privacy and responsible use" icon={<ShieldCheck size={17} />}>
        <div className="about-text">
          <p>
            {ws.hosted
              ? webPrivacy + ' Search history is optional and saved in this browser.'
              : 'HuntWick checks publicly accessible profile pages. Each selected platform can see your IP address and the requested username. Search history is optional and stored on this device.'}
          </p>
          <p>
            A matching username can belong to a different person. Verify findings independently and respect
            platform terms, privacy and applicable law.
          </p>
        </div>
      </Panel>
    </>
  )
}

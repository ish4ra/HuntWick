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
import { isActive, Toggle, version, type Workspace } from './common'

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
  const [confirmClear, setConfirmClear] = useState(false)
  return (
    <>
      <Intro
        label="PREFERENCES"
        title="Settings"
        description="Manage your workspace appearance, search defaults and local history."
      />
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
      <Panel title="Search defaults" icon={<SlidersHorizontal size={17} />}>
        <Preference
          title="Remember search preferences"
          hint="Keep your search limits and default mode between app sessions."
        >
          <Toggle
            checked={s.rememberPreferences}
            label="Remember search preferences"
            onChange={() => ws.updateSettings({ rememberPreferences: !s.rememberPreferences })}
          />
        </Preference>
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
        <div className="pref-numbers">
          <NumberSetting
            label="Timeout per platform (seconds)"
            value={s.timeout}
            min={1}
            max={60}
            onChange={(timeout) => ws.updateSettings({ timeout })}
          />
          <NumberSetting
            label="Concurrent platform checks"
            value={s.concurrency}
            min={1}
            max={20}
            onChange={(concurrency) => ws.updateSettings({ concurrency })}
          />
        </div>
      </Panel>
      <Panel title="Privacy" icon={<LockKeyhole size={17} />}>
        <Preference
          title="Save search history"
          hint="Store completed searches on this device for later review."
        >
          <Toggle
            checked={s.saveHistory}
            label="Save search history"
            onChange={() => ws.updateSettings({ saveHistory: !s.saveHistory })}
          />
        </Preference>
        <p className="settings-note">
          Search requests go directly to the selected platforms, which can see your IP address and the
          username you check.
        </p>
        <Preference
          title="Clear local application data"
          hint="Remove saved searches and preferences from this device."
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
        description="An open-source desktop workspace for public profile discovery."
      />
      <section className="about-brand">
        <img src="/huntwick.svg" alt="" />
        <div>
          <h2>HuntWick</h2>
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
        <div className="about-row">
          <Github size={16} />
          <span>Source repository</span>
          <button
            className="text-action"
            onClick={() => void ws.openUrl('https://github.com/ish4ra/HuntWick')}
          >
            ish4ra/HuntWick <ExternalLink size={13} />
          </button>
        </div>
      </Panel>
      <Panel title="Privacy and responsible use" icon={<ShieldCheck size={17} />}>
        <div className="about-text">
          <p>
            HuntWick checks publicly accessible profile pages. Each selected platform can see your IP address
            and the requested username. Search history is optional and stored on this device.
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

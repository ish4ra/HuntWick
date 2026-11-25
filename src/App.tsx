import { Updates } from "./ui/Updates"
import { useCallback, useEffect, useState } from 'react'
import {
  AlertCircle,
  ChevronRight,
  CircleHelp,
  Database,
  Fingerprint,
  ExternalLink,
  Github,
  Globe2,
  History,
  Info,
  Menu,
  Monitor,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings2,
  ShieldCheck,
  X,
} from 'lucide-react'
import { useHuntWick } from './useHuntWick'
import { HistoryPage, PlatformsPage } from './ui/LibraryPages'
import { AboutPage, SettingsPage } from './ui/Preferences'
import SearchPage from './ui/SearchPage'
import { desktopDownloadsUrl, repositoryUrl, version, type Page } from './ui/common'

const workspaceLinks = [
  { page: 'Search', Icon: Search },
  { page: 'History', Icon: History },
  { page: 'Platforms', Icon: Database },
] as const
const appLinks = [
  { page: 'Settings', Icon: Settings2 },
  { page: 'About', Icon: Info },
] as const
export default function App() {
  const ws = useHuntWick()
  const [page, setPage] = useState<Page>('Search')
  const [collapsed, setCollapsed] = useState(false)
  const [mobileMenu, setMobileMenu] = useState(false)
  const [focusToken, setFocusToken] = useState(0)
  const navigate = useCallback((next: Page) => {
    setPage(next)
    setMobileMenu(false)
    window.scrollTo(0, 0)
  }, [])
  useEffect(() => {
    function shortcut(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        navigate('Search')
        setFocusToken((t) => t + 1)
      }
      if (event.key === 'Escape') setMobileMenu(false)
    }
    window.addEventListener('keydown', shortcut)
    return () => window.removeEventListener('keydown', shortcut)
  }, [navigate])
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = () => {
      document.documentElement.dataset.theme =
        ws.settings.theme === 'system' ? (media.matches ? 'dark' : 'light') : ws.settings.theme
    }
    apply()
    media.addEventListener('change', apply)
    return () => media.removeEventListener('change', apply)
  }, [ws.settings.theme])
  function navLink({ page: target, Icon }: (typeof workspaceLinks | typeof appLinks)[number]) {
    return (
      <button
        key={target}
        className={'nav-link' + (page === target ? ' current' : '')}
        aria-label={target}
        title={collapsed ? target : undefined}
        aria-current={page === target ? 'page' : undefined}
        onClick={() => navigate(target)}
      >
        <Icon size={18} />
        <span>{target}</span>
        {page === target && <span className="nav-current-dot" />}
      </button>
    )
  }
  return (
    <div
      className={'app' + (collapsed ? ' sidebar-collapsed' : '') + (mobileMenu ? ' menu-open' : '')}
      data-density={ws.settings.density}
    >
      <a className="skip" href="#main">
        Skip to content
      </a>
      {mobileMenu && (
        <button className="mobile-scrim" onClick={() => setMobileMenu(false)} aria-label="Close navigation" />
      )}
      <aside className="sidebar" aria-label="Main navigation">
        <div className="brand">
          <img src="/huntwick.svg" alt="" />
          <div>
            <span className="wordmark" role="img" aria-label="HuntWick" />
            <small>OSINT, simplified.</small>
          </div>
          <button
            className="mobile-close icon-button"
            aria-label="Close navigation"
            onClick={() => setMobileMenu(false)}
          >
            <X size={17} />
          </button>
        </div>
        <nav>
          <div className="nav-group">
            <p>Workspace</p>
            {workspaceLinks.map(navLink)}
          </div>
          <div className="nav-group">
            <p>Application</p>
            {appLinks.map(navLink)}
          </div>
        </nav>
        <div className="sidebar-bottom">
          <div className="local-card">
            <span className="local-icon">
              <ShieldCheck size={17} />
            </span>
            <div>
              <strong>{ws.hosted ? 'Web workspace' : 'Local workspace'}</strong>
              <small>{ws.hosted ? 'Private preview' : 'Runs on this device'}</small>
            </div>
          </div>
          <div className="version-line">
            <span className="version-tag">v{version}</span>
            <button
              className="icon-button collapse"
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            </button>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <button
            className="mobile-toggle icon-button"
            aria-label="Open navigation"
            onClick={() => setMobileMenu(true)}
          >
            <Menu size={19} />
          </button>
          <div className="breadcrumb">
            <>{ws.hosted ? <Globe2 size={17} /> : <Fingerprint size={17} />}</>
            <span>{ws.hosted ? 'HuntWick Web' : 'Workspace'}</span>
            <ChevronRight size={13} />
            <strong>{page}</strong>
          </div>
          <div className="top-right">
            {ws.hosted ? (
              <div className="web-header-links">
                <a href={repositoryUrl} target="_blank" rel="noreferrer" aria-label="HuntWick on GitHub">
                  <Github size={15} />
                  <span>GitHub</span>
                </a>
                <a
                  href={desktopDownloadsUrl}
                  target="_blank"
                  rel="noreferrer"
                  aria-label="Get HuntWick desktop installers"
                >
                  <Monitor size={15} />
                  <span>Get desktop</span>
                  <ExternalLink size={11} />
                </a>
              </div>
            ) : (
              <span className="desktop-label">
                <Monitor size={13} />
                {ws.desktop ? 'Desktop edition' : 'Desktop preview'}
              </span>
            )}
            <i className="separator" />
            <button
              className="icon-button"
              title="About HuntWick"
              aria-label="About HuntWick"
              onClick={() => navigate('About')}
            >
              <CircleHelp size={16} />
            </button>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <div className="main-inner">
            {ws.error && (
              <div className="error-banner" role="alert">
                <AlertCircle size={17} />
                <span>{ws.error}</span>
                {!ws.catalog && (
                  <button className="text-action" onClick={() => void ws.retryCatalog()}>
                    Retry
                  </button>
                )}
                <button className="icon-button" aria-label="Dismiss message" onClick={ws.clearError}>
                  <X size={14} />
                </button>
              </div>
            )}
            {page === 'Search' && <SearchPage ws={ws} focusToken={focusToken} />}
            {page === 'History' && <HistoryPage ws={ws} navigate={navigate} />}
            {page === 'Platforms' && <PlatformsPage ws={ws} />}
            {ws.desktop && <Updates ws={ws} visible={page === 'Settings' || page === 'About'}/ >}
            {page === 'Settings' && <SettingsPage ws={ws} />}
            {page === 'About' && <AboutPage ws={ws} />}
          </div>
        </main>
      </div>
    </div>
  )
}

import { describe, expect, it } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { PlatformMark, resolvePlatformLogo } from './ui/PlatformMark'

describe('local catalog logo identities', () => {
  it.each([
    ['Laracast', 'laracasts'], ['X (Twitter)', 'x'], ['KO-FI', 'kofi'], ['replit.com', 'replit'],
    ['My Anime List', 'myanimelist'], ['Docker Hub', 'docker'], ['WATTPAD', 'wattpad'],
    ['Kongregate', 'kongregate'], ['LibraryThing', 'librarything'], ['LiveJournal', 'livejournal'],
    ['LeetCode', 'leetcode'], ['Mixcloud', 'mixcloud'], ['Medium', 'medium'], ['Kwork', 'kwork'],
    ['mastodon.social', 'mastodon'], ['mastodon.online', 'mastodon'], ['MSTDN.PARTY', 'mastodon'],
    ['lemmy.ml', 'lemmy'], ['arcgit.wpi.edu', 'gitlab'], ['8cubes.com', 'gitea'],
    ['git.gay', 'forgejo'], ['1160.theshizz.org', 'discourse'], ['bbs.6ebook.com', 'flarum'],
    ['Codeberg', 'codeberg'], ['iNaturalist', 'inaturalist'],
  ])('resolves %s from catalog evidence', (name, expected) => {
    expect(resolvePlatformLogo(name)).toBe(expected)
  })
  it('only assigns family logos to known instance identities', () => {
    for (const name of ['unknown.example', 'gitlab.unlisted.example', 'mstdn-party','__proto__']) {
      expect(resolvePlatformLogo(name)).toBeUndefined()
      const mark = renderToStaticMarkup(createElement(PlatformMark, { name }))
      expect(mark).toContain('class="platform-mark"')
      expect(mark).not.toMatch(/url\(|src=/)
    }
  })
})

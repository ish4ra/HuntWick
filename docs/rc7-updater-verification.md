# Update checks and published release notes

A manual **Check for updates** reads the stable and preview feeds. With prereleases off, an eligible stable release takes priority. If only a newer preview is available, Settings shows its version and a **Check prerelease** button. This button checks again and authorizes a preview offer for this check only. The saved preference still controls startup behavior. Installation requires a separate restart confirmation and the native signature check.

The native command retains only an eligible, explicitly selected update for installation. A preview notice carries just a version string. Each channel reports an unpublished feed, a connection failure or invalid metadata independently. A missing or failing feed cannot produce the “No newer update is available” message. A valid offer from the other channel can still be shown alongside that feed status.

## Published RC.6 notes

On 28 November 2026, the RC.6 release manifest and active preview manifest shared SHA-256 `733351e014ca4e14ae7f1981f4fb1b681b9da1284065e77e4a2e298fae91559b`. Stable returned HTTP 404. Both manifests decode to the same notes with actual line breaks, a version paragraph, six headings and eight bullets. The fixture is the exact UTF-8 text of the decoded notes field, including the trailing newline. [Release manifest](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/latest.json) · [Preview manifest](https://github.com/ish4ra/HuntWick/releases/download/updates-preview/latest.json) · [Fixture](../scripts/fixtures/update/rc6-published-notes.md)

The existing RC.6 renderer displays those notes as headings and lists. The owner saw the older RC.5 renderer during the upgrade. The Chromium check uses the published notes in both themes, checks scrolling at a 700 × 650 viewport and verifies that HTML stays visible as text. The preview notice screenshots use a synthetic newer version and a missing stable feed.

| View | Light | Dark |
| --- | --- | --- |
| Published release notes | [Light notes](rc7-media/updater/light/published-rc6-notes.png) | [Dark notes](rc7-media/updater/dark/published-rc6-notes.png) |
| Preview notice | [Light notice](rc7-media/updater/light/prerelease-notice.png) | [Dark notice](rc7-media/updater/dark/prerelease-notice.png) |

Run `npm run build` followed by `python scripts/check_updater_ui.py` for browser checks with fixture IPC. Rust unit tests cover installed-version and channel precedence. The existing Linux AppImage workflow also checks that invoking installation directly from a preview notice is rejected. The screenshots exercise the frontend. Installed-client validation of the changed native command belongs to the next candidate build.

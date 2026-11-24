# RC.2 desktop acceptance

The Windows NSIS installer, both macOS DMGs, the Debian package and the AppImage carry version 0.1.0-rc.2. The matrix checked each installed desktop and its bundled Sherlock runtime. On macOS it mounted the DMG and launched the application from the mounted volume. On Linux it also checked the AppImage engine and exercised automatic restart after an update. [Desktop CI](https://github.com/ish4ra/HuntWick/actions/runs/45507665646)

## Downloads

Sign in to GitHub to download Actions artifacts. Verify the ZIP digest before extracting it. Verify the installer with the target-specific SHA256SUMS file inside. CI also verifies each native updater's Ed25519 signature and signed version. The macOS checksum manifests include both the DMG and the signed app archive.

| Platform and installers | Download | ZIP SHA256 |
| --- | --- | --- |
| Apple Silicon · DMG | [ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45507665646/artifacts/14974347358) | `57cab309ad10bf6950e8886781b42d9a48a57442f4974cb6acd9937d4f4236bd` |
| Intel Mac · DMG | [ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45507665646/artifacts/14975540718) | `2bdf860aeead898a6cd3bc7f292c087793b4a4dae636e1c5e5563d962240fcc2` |
| Windows x64 · NSIS | [ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45507665646/artifacts/14974637567) | `2f28c86bf7b1f90664426a1705d7e2f13e84ba2b3df38e7efd05efba50f294a6` |
| Linux x64 · Debian and AppImage | [ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45507665646/artifacts/14974282846) | `7e836e45dc94f7d41b84515c36fcfe430022756c2ae0337a064b24e97a3ef97c` |

## Updater evidence

The Linux fixture built an older installed client from the candidate updater source with version RC.1, an ephemeral verification key and a loopback HTTPS endpoint. The server used an independent private CA and a non-CA server certificate with a loopback IP subject alternative name. The installed client rejected a missing manifest, a preview on the stable channel, a downgrade, an unavailable platform and an invalid package signature. It then downloaded and installed signed RC.2. The fixture compared the complete installed bytes with the candidate and waited for the restarted candidate to confirm its bundled catalog and rendered search form.

The first installed-client fixture checked WebKit storage for its preference and history sentinels after restart. A subsequent matrix adds a complete saved search, a native download-event assertion and verification of the archive bytes downloaded back from GitHub. [Follow-up run](https://github.com/ish4ra/HuntWick/actions/runs/45510604301) The separate Chromium interface check used fixture IPC to exercise a stable startup notification, manual preview selection, progress display, error recovery, the manual-download destination and the install-button lock during an active search. Run it with a built frontend, Chromium and Python Playwright using `python scripts/check_updater_ui.py`.

On both Mac architectures Tauri now builds the app bundle explicitly alongside the DMG. CI requires exactly one native `.app.tar.gz` and its signature. Windows and Linux use the version-bound signed NSIS and AppImage payloads. CI signing keys are disposable. The release workflow requires the owner's production public key and private signing secrets. [Signing and manual installation](packaging.md)

## Owner checks before promotion

1. Install the matching candidate on a representative device, verify the checksums, launch it and open a public profile you are authorized to test.
2. For the timeout investigation, repeat the earlier selection on the same network with the same authorized handle, timeout, concurrency and catalog settings. Record elapsed time and all result counts. Use **Export → Export diagnostics (no handle or URLs)** and review the platform list before sharing. The earlier 121 timeouts over 9 minutes 45 seconds remain an open live-network measurement. [Diagnostic fields and limits](catalog-audit.md#measuring-an-owner-side-run)
3. Exercise a two-version update on representative Windows and macOS devices before approving those in-place upgrade paths. Check download progress, restart, retained preferences and a saved search. Confirm manual recovery through a checksummed installer.
4. Select a wordmark proposal if desired. The three review studies are separate from the installed identity. The README radar uses SVG/CSS discovery markers with a static PNG alternative. [Wordmark PNGs and vectors](magnifier-review/README.md)
5. Create and back up the production signing key on an owner-controlled machine. Set repository variable `UPDATER_PUBLIC_KEY` and Actions secrets `UPDATER_PRIVATE_KEY` and `UPDATER_KEY_PASSWORD`. A build embedding that public key is required for production updates. Approve the release version, channel and publication separately. [Release checklist](release-checklist.md)

Web Edition remains at its last passing private-preview checkpoint. The hosted search allowlist, radar and default-off sounds are unchanged by the desktop packaging corrections. [Web CI](https://github.com/ish4ra/HuntWick/actions/runs/45430038678)

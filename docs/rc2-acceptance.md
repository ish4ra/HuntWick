# RC.2 desktop acceptance

CI tested commit `afaac5d771cef676a5bf919d280dd09674d88757`. The Windows NSIS installer, both macOS DMGs, the Debian package and the AppImage carry version 0.1.0-rc.2. The matrix checked each installed desktop and its bundled Sherlock runtime. On macOS it mounted the DMG and launched the application from the mounted volume. On Linux it also checked the AppImage engine and exercised automatic restart after an update. [Desktop CI](https://github.com/ish4ra/HuntWick/actions/runs/45512861729)

## Downloads

Sign in to GitHub to download Actions artifacts. Each packaging job downloaded the uploaded ZIP from GitHub and independently matched its SHA256 to the upload digest. Verify the ZIP digest before extracting it. Verify the installer with the target-specific SHA256SUMS file inside. CI also verifies each native updater's Ed25519 signature and signed version. The macOS checksum manifests include both the DMG and the signed app archive.

| Platform and installers | Download | ZIP SHA256 |
| --- | --- | --- |
| Apple Silicon · DMG | [ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45512861729/artifacts/14976703708) | `1dc3d991d55f201d0daa91c7587ffd165ea005869f50627a63f3c6f27d8983ed` |
| Intel Mac · DMG | [ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45512861729/artifacts/14976938869) | `04a8c7b3639740f99be414283a2d8bf2cc7501b17e5bdec711323325aa51f71d` |
| Windows x64 · NSIS | [ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45512861729/artifacts/14977092830) | `7582e515fe39fca7483a227b84e1a1b7676fd69f7d191ae1fc6334e710783ab2` |
| Linux x64 · Debian and AppImage | [ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45512861729/artifacts/14976987546) | `c8b74d53eadda998da9ac8f8db124114e14b624116bbb3497c3e654180f05c50` |

## Updater evidence

The Linux fixture built an older installed client from the candidate updater source with version RC.1, an ephemeral verification key and a loopback HTTPS endpoint. The server used an independent private CA and a non-CA server certificate with a loopback IP subject alternative name. The installed client rejected a missing manifest, a preview on the stable channel, a downgrade, an unavailable platform and an invalid package signature. It then downloaded and installed signed RC.2. The fixture compared the complete installed bytes with the candidate and waited for the restarted candidate to confirm its bundled catalog and rendered search form.

The installed-client fixture also observed download events and checked WebKit storage for the fixture's light theme, history preference and synthetic completed search after restart. The separate Chromium interface check used fixture IPC to exercise a stable startup notification, manual preview selection, progress display, error recovery, the manual-download destination and the install-button lock during an active search. Run it with a built frontend, Chromium and Python Playwright using `python scripts/check_updater_ui.py`.

On both Mac architectures Tauri now builds the app bundle explicitly alongside the DMG. CI requires exactly one native `.app.tar.gz` and its signature. Windows and Linux use the version-bound signed NSIS and AppImage payloads. CI signing keys are disposable. The release workflow requires the owner's production public key and private signing secrets. [Signing and manual installation](packaging.md)

## Owner checks before promotion

1. Install the matching candidate on a representative device, verify the checksums, launch it and open a public profile you are authorized to test.
2. For the timeout investigation, repeat the earlier selection on the same network with the same authorized handle, timeout, concurrency and catalog settings. Record elapsed time and all result counts. Use **Export → Export diagnostics (no handle or URLs)** and review the platform list before sharing. The earlier 121 timeouts over 9 minutes 45 seconds remain an open live-network measurement. [Diagnostic fields and limits](catalog-audit.md#measuring-an-owner-side-run)
3. Exercise a two-version update on representative Windows and macOS devices before approving those in-place upgrade paths. Check download progress, restart, retained preferences and a saved search. Confirm manual recovery through a checksummed installer.
4. Select a wordmark proposal if desired. The three review studies are separate from the installed identity. The README radar uses SVG/CSS discovery markers with a static PNG alternative. [Wordmark PNGs and vectors](magnifier-review/README.md)
5. Create and back up the production signing key on an owner-controlled machine. Set repository variable `UPDATER_PUBLIC_KEY` and Actions secrets `UPDATER_PRIVATE_KEY` and `UPDATER_KEY_PASSWORD`. A build embedding that public key is required for production updates. Approve the release version, channel and publication separately. [Release checklist](release-checklist.md)

Web Edition remains at its last passing private-preview checkpoint. The web candidate uses its hosted search allowlist, event-driven radar and default-off sounds. [Web CI](https://github.com/ish4ra/HuntWick/actions/runs/45430038678)

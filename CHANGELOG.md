# Changelog

## 0.1.0-rc.6

Published to the preview channel for Apple Silicon, Intel Mac, Windows x64 and Linux x64. [Public release](https://github.com/ish4ra/HuntWick/releases/tag/v0.1.0-rc.6) · [Verified files and rollback manifests](docs/rc6-production.md)

### Discovery

- Full Search remains the default. Deep Search combines up to 4,552 eligible profile routes with standard settings, or 4,569 with adult sites enabled. New routes include Codementor and HackingWithSwift. Scratch's public API can verify a matching username and account ID.

### Search reliability

- Complementary providers share a per-profile deadline. Deep Search preserves overlapping verdicts and handles fully qualified Bluesky names. Discourse JSON matches require the requested username and an integer user ID.
- DNS, TLS and proxy failures have distinct outcomes. Connection failures and timeouts can be retried from Results.

### Search interface

- A single persistent switch controls adult-platform inclusion. Large searches show workload, pending checks, throughput and estimated time remaining. Cancellation is available from Results.
- The radar fits narrower windows, and more platforms have local icons.

### Software updates

- One update action checks the selected channels. The prerelease preference is remembered. The newest eligible version is offered, with formatted release notes, transfer progress and restart confirmation.

### Branding

- The approved Pivot icon and two-tone wordmark bring the optical magnifier into the H crossbar and lowercase i across desktop, web and installers.

### Known limitations

- Additional live matches have not been established in the cloud tests. Proxy denials prevented origin verification. Eligible routes can time out or block access. SpankBang has no validated bundled rule.

## 0.1.0-rc.5

- Bundle Maigret 0.6.7 alongside Sherlock, with progressive Deep Search and source verdicts.
- Search 4,550 unique eligible profiles with default category settings. Review workload, change engine or cancel in the console.
- Add targeted retries, visible desktop adult-category consent and paginated results.

## 0.1.0-rc.4 — release candidate

- Restore Sherlock methods and original verdicts on desktop. Show provider claims and conflicting evidence alongside independently verified matches.
- Add Enhanced Search with public platform routes, bounded transport workers, an optional transient retry and versioned catalog provenance.
- Add circular radar blips, separate scanning and detection sounds and per-cue previews. Integrate signed updates and restart confirmation into Settings.

## 0.1.0-rc.3 — release candidate

- Apply the approved Cut wordmark and Counter icon to both editions, native packages and README artwork.
- Build artifact-only desktop candidates from the combined desktop and web source. Installed startup checks validate the candidate version and the permanent updater key.

## 0.1.0-rc.2 — unreleased

- Added opt-in desktop catalog policies, per-platform diagnostics and a handle-free diagnostic export.
- Added signed-update controls, live discovery markers, optional detection tones and bundled platform artwork.
- Private web searches retain the two-platform allowlist.

## 0.1.0-rc.1 — unreleased

- Add a local Tauri and React workspace for public username discovery with a bundled Sherlock engine and pinned platform definitions.
- Stream results into filterable table and card views. Add cancellation, per-site selection, local exports and opt-in history.
- Add desktop branding, light and dark themes, scoped native IPC and deterministic protocol, privacy and export tests.
- Add native packaging workflows for Windows x64, macOS arm64 and x64, and Linux x64. See the run for each commit for available artifacts.
- Include the original UTC search timestamp on every CSV row. Verify installed GUI startup and individual installer hashes during packaging.

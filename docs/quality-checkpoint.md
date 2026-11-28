# Search quality and release gates

Stable promotion is on hold pending review of discovery coverage, confidence and diagnostic counts. The owner has exercised Full Search on physical macOS hardware. That observation establishes a real investigation need; it does not identify which site rules are inaccurate. Keep individual handles, profile links and owner results out of fixtures and public reports.

| Priority | Integration gate |
| --- | --- |
| P0 | Web recovery checkpoint fa1a446 includes the restricted service, browser bridge, interface and packaging recipe. |
| P1 | Compare official Sherlock semantics, distinguish verified from possible leads, expose unavailable mainstream services and their reasons, test every terminal category and preserve legacy history. |
| P2 | Validate authenticated browser streaming/export, cancellation, budgets and Docker CI. Hosted routes remain explicitly allowlisted. |
| P3 | Measure bounded network and engine overhead with deterministic inputs; review original identity concepts before replacing assets; validate the animated README. |
| P4 | Rebuild and verify candidate installers for behavior changes. Complete owner review of quality and representative hardware before stable approval. The earlier RC matrix applies to its tested source only. |

## Quality candidate

The offline parity suite runs the official Sherlock 0.16.2 CLI and adapter against 13 identical HTTP fixtures. Sherlock reported claimed for generic HTML, an echoed handle and a login page. HuntWick retains uncertainty or reports the restriction. A matching canonical URL plus a handle-led title can produce a possible match. Stronger account metadata can verify it. The interface separates all eight outcomes and reads earlier saved runs. Historical counts alone cannot reconstruct which websites returned which response.

TikTok and YouTube use structured owner metadata on their public profile pages. Instagram and X rules use third-party mirrors, Reddit appears in upstream exclusions and Facebook lacks a bundled rule. The desktop directory explains these exclusions. Hosted checks remain limited to the two approved routes.

Five-run median source-engine measurements on Linux used synthetic 16 KiB pages, 8 ms simulated transport and eight workers. Deferring Sherlock’s dataframe dependency until search reduced catalog completion from 872 to 309 ms. Quick completion moved from 754 to 865 ms and Full from 1264 to 1177 ms. Cancellation after worker readiness measured 6.8 and 6.6 ms. These measurements exclude live network latency. Reproduce with engine/tests/profile_search.py and compare identical environments.

Next gates are reviewing candidate artifacts, owner testing on representative hardware, restricted hosting validation and owner selection of an identity from the review board.

## Updated RC installers

All four jobs passed for 98e2235. The installed-engine checks and desktop startup probes passed on each runner. The package version remains 0.1.0-rc.1. Use the run and archive digest to identify this quality build. [Desktop CI](https://github.com/ish4ra/HuntWick/actions/runs/45379312570)

| Installer archive | GitHub archive SHA256 |
| --- | --- |
| [huntwick-aarch64-apple-darwin](https://github.com/ish4ra/HuntWick/actions/runs/45379312570/artifacts/14914720640) | `fb3db359da449d2232bdb72eaae0e119589fedb9b7d4d5909cd62e47be1b8f2f` |
| [huntwick-x86_64-apple-darwin](https://github.com/ish4ra/HuntWick/actions/runs/45379312570/artifacts/14914417896) | `feb6c68451f7ebf6fb93019b3f5c25f6da13a58c83457d9fde0d27edb20546e1` |
| [huntwick-x86_64-pc-windows-msvc](https://github.com/ish4ra/HuntWick/actions/runs/45379312570/artifacts/14913487308) | `e763a87793397981ceb3d4bed163513c82747df8bdb5c7f1d28e597fa2016112` |
| [huntwick-x86_64-unknown-linux-gnu](https://github.com/ish4ra/HuntWick/actions/runs/45379312570/artifacts/14914775922) | `eea40404d5ee0db47369bc215793bd438b9aa303fa8a5c3171d3cf1f5352a700` |

Extract the archive and verify the individual installer against its included manifest. Owner acceptance on representative devices and a release decision remain pending.

## Web verification

Web CI passed on the code at 72e0a3a. The local production image also passed authenticated HTTP and Chromium checks under a 512 MiB container limit. The smoke selected GitHub alone and used a synthetic handle that its rule rejects before network I/O. The browser rendered that result and exported the matching CSV. The same image denied anonymous access and enforced the six-search budget. Backend fixtures cover disconnect cleanup and cancellation. The next deployment step requires an authorized Render workspace and deployment approval. [Web CI run](https://github.com/ish4ra/HuntWick/actions/runs/45377424404) · [Owner deployment steps](web-deployment.md)

The production web workflow passed again on 60a337f after moving the search runtime initialization ahead of the parent-pipe watcher. The workflow builds the production image and tests its authenticated HTTP stream and browser CSV download. Provider cold start, memory at peak concurrency and streaming through its HTTPS proxy still need a deployed private preview. [Updated Web CI](https://github.com/ish4ra/HuntWick/actions/runs/45379328939)

## Interactive web radar

Run 45430038678 passed the production container checks, offline authenticated search, CSV export, and Chromium radar regression. A synthetic two-platform event stream produced one verified and one possible marker even with a duplicate event. Keyboard focus revealed the possible match. The default scheduled zero oscillator tones, and enabling sound scheduled one for the burst. The desktop and mobile radar screenshots use these synthetic events. Provider deployment remains an owner decision. [Web CI](https://github.com/ish4ra/HuntWick/actions/runs/45430038678)

# Main branch integration review

The candidate branch is `integration/desktop-web`. Its merge commits preserve the histories of desktop `a7ea0ee` and web `9eecb98`. The target is the existing `main` branch. The animated README leads with the verified desktop RC.2 download and separately describes the authenticated Web Edition and its pending deployment.

## Conflict decisions

| Area | Integrated behavior |
| --- | --- |
| Shared React model and session | Desktop retains both independent catalog controls, its full concurrency and timeout ranges, updater IPC and local diagnostics. The web build selects its authenticated HTTP bridge, caps concurrency at two and sends searches to the hosted allowlist. |
| Search and Platforms | Hosted users choose enabled sites from GitHub and GitLab. Quick Search, the unavailable platform list and catalog expansion belong to the desktop UI. The service validates the request again before starting the worker. |
| Appearance and application information | Shared responsive styles, icons and radar coexist with the native updates UI. The shared application info points to verified RC.2 downloads and displays privacy information for the active transport. |
| Engine and tests | Kept the portable desktop Sherlock CLI comparison test and native protocol. Hosted responses project only approved platform, URL and status fields. Service tests reject desktop policy flags and out-of-catalog sites. |
| Documentation and workflows | Preserved both quality records, both privacy descriptions and the owner signing gate. Integration pushes run native checks without installer packaging. Web changes on a PR are eligible for the restricted Docker and browser jobs. Main pushes can build CI artifacts. Publication requires a separate owner action. |

## Verification on the combined source

- TypeScript, ESLint and Vite passed. All 43 frontend tests passed, including hosted transport and shared result handling.
- Nine service tests, 22 engine tests, eight Rust tests, four packaging-script tests and four version-bound signature tests passed. The new service regression sent desktop catalog overrides to the hosted API and confirmed rejection before a worker started.
- A fresh restricted Docker image passed the authentication, two-route catalog, offline engine search, rate-limit and log-privacy checks. Chromium exercised the hosted search, CSV export, radar markers and optional sound. A separate built desktop-interface test used fixture IPC to check updater offers, progress, recovery and the active-search interlock.
- These checks used synthetic inputs. The owner's earlier 121 timeouts in 9 min 45 s require measurements from the owner's network. [Diagnostic procedure](catalog-audit.md#measuring-an-owner-side-run)

## Owner review order

1. Select the [wordmark](letterform-review/README.md) and [standalone icon](app-icon-review/README.md) independently. Apply the approved assets to desktop, web, the sidebar, platform icon packages, favicon and both README hero forms. Preserve previous studies in the review archive.
2. Prepare RC.3 on the desktop branch. Advance the artifact-only production build ref to the reviewed version commit after authorization. Require all four platform jobs, five installers, native signatures, per-file manifests, ZIP digests and matching public-key fingerprints. Record the exact commit and retain those exact bytes with the run ID and digests before Actions retention expires. Only RC.2 installers exist at this checkpoint. [Production updater procedure](production-updater.md)
3. Bring the final approved desktop and web commits into this integration branch by merging. Re-run the affected checks on the final tree and review the README, privacy boundaries and download targets against the selected release artifacts. Keep the proposal in draft until the owner approves the exact integration SHA.
4. To put the reviewed project on main, use **Create a merge commit** on the integration PR. Retain both development branches. Confirm that main contains both input histories, renders the animated README and points to the correct candidate. This operation does not publish a GitHub release or deploy the web service.
5. Obtain separate approval to publish a separately verified RC.4 prerelease and its preview feed. Test RC.3 → RC.4 in-app before recording production device acceptance. Stable promotion, DNS and hosting have independent owner gates.

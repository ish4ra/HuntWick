# Main branch integration review

The candidate branch is `integration/desktop-web`. Its merge commits preserve the histories of desktop `a7ea0ee` and web `9eecb98`. The target is the existing `main` branch. The animated README leads with the desktop RC.3 acceptance record and separately describes the authenticated Web Edition and its pending deployment.

## Conflict decisions

| Area | Integrated behavior |
| --- | --- |
| Shared React model and session | Desktop retains both independent catalog controls, its full concurrency and timeout ranges, updater IPC and local diagnostics. The web build selects its authenticated HTTP bridge, caps concurrency at two and sends searches to the hosted allowlist. |
| Search and Platforms | Hosted users choose enabled sites from GitHub and GitLab. Quick Search, the unavailable platform list and catalog expansion belong to the desktop UI. The service validates the request again before starting the worker. |
| Appearance and application information | Shared responsive styles, icons and radar coexist with the native updates UI. The shared application info points to RC.3 downloads and displays privacy information for the active transport. |
| Engine and tests | Kept the portable desktop Sherlock CLI comparison test and native protocol. Hosted responses project only approved platform, URL and status fields. Service tests reject desktop policy flags and out-of-catalog sites. |
| Documentation and workflows | Preserved both quality records, both privacy descriptions and the owner signing gate. Integration pushes run native checks without installer packaging. The Web workflow runs the restricted Docker and Chromium checks on integration pushes. Main pushes can build CI artifacts. Publication requires a separate owner action. |

## Verification on the combined source

- TypeScript, ESLint and Vite passed. All 43 frontend tests passed, including hosted transport and shared result handling.
- Nine service tests, 22 engine tests, eight Rust tests, four packaging-script tests and four version-bound signature tests passed. The new service regression sent desktop catalog overrides to the hosted API and confirmed rejection before a worker started.
- A fresh restricted Docker image passed the authentication, two-route catalog, offline engine search, rate-limit and log-privacy checks. Chromium exercised the hosted search, CSV export, radar markers and optional sound. A separate built desktop-interface test used fixture IPC to check updater offers, progress, recovery and the active-search interlock.
- These checks used synthetic inputs. The owner's earlier 121 timeouts in 9 min 45 s require measurements from the owner's network. [Diagnostic procedure](catalog-audit.md#measuring-an-owner-side-run)

## Owner review order

1. Review the integrated change set and release evidence. The signed candidate uses the same desktop and web implementation as the proposed main branch. The production build ref preserves the exact packaging commit. [RC.3 acceptance and downloads](rc3-acceptance.md)
2. Open a draft PR from `integration/desktop-web` to `main` and record the reviewed SHA. The cloud proxy returned HTTP 403 for GitHub's PR API. [Open the comparison](https://github.com/ish4ra/HuntWick/compare/main...integration/desktop-web?expand=1)
3. After owner approval, choose **Create a merge commit** to retain both histories. Review the README and RC.3 download links on main after the merge.
4. Install RC.3 manually. Approval for an RC.4 prerelease and preview feed is a separate decision. Verify an in-app upgrade on representative macOS and Windows devices before stable promotion. Web hosting and the custom domain await owner approval. [Production updater procedure](production-updater.md)

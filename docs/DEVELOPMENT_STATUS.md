# HuntWick v0.1.0 development status

## November 23 release validation

The development branch is `feat/phase-1-desktop-mvp`. The first complete application checkpoint is `83c76a9`. All four jobs for `4f8ae0c0c61a45e12d7f59e357f44700a15dcf55` built the alpha installers and executed their bundled Sherlock engines. The archives, digests and manual tests are listed in the [release checklist](release-checklist.md).

| Area | Evidence |
| --- | --- |
| Interface | ESLint, TypeScript, Vite production build and 34 Vitest cases passed. Browser checks covered all five pages, two viewport sizes, sorting, filters, views, clipboard, themes and local storage. |
| Engine | 15 deterministic Python tests passed, including status classification, corrupt snapshot rejection and pipe closure on parent loss. The stock CPython 3.12.14 Linux build loaded 396 compatible sites, including 12 Quick sites, without Python on PATH. A synthetic single-site GitHub lookup returned not found and completed with certificate verification enabled. |
| Native host | Linux Tauri debug build displayed the Search page and read the complete catalog. The host and engine now use a liveness pipe so closing the host during a search terminates the worker. |
| Functional scope | Public handle discovery, progressive results, cancellation, native HTTPS opening, exports and opt-in local history. An inconclusive result can represent a real profile whose page lacks enough evidence to confirm a match. |
| Installer verification | The `0.1.0-rc.1` changes add a test-only launch flag for the shipped GUI, enabled explicitly by the caller. A successful exit requires the webview to render Search and load the native catalog. The matrix checks individual installer hashes before artifact upload. |
| Pull request | Git push works. An HTTPS CONNECT to api.github.com returned HTTP 403 from the cloud proxy. A restricted-network draft adds this single host. Manual draft PR creation is available through the [branch comparison](https://github.com/ish4ra/HuntWick/compare/main...feat/phase-1-desktop-mvp?expand=1). |

Keep the RC version until final platform results and remaining interactive acceptance checks are recorded. The stable version, merge and publication await review.

# HuntWick v0.1.0 development status

## November 23 release validation

The development branch is `feat/phase-1-desktop-mvp`. The first complete application checkpoint is `83c76a9`. All four jobs for `4f8ae0c0c61a45e12d7f59e357f44700a15dcf55` built the alpha installers and executed their bundled Sherlock engines. The archives, digests and manual tests are listed in the [release checklist](release-checklist.md).

| Area | Evidence |
| --- | --- |
| Interface | ESLint, TypeScript, Vite production build and 35 Vitest cases passed. Browser checks covered all five pages, two viewport sizes, sorting, filters, views, clipboard, themes and local storage. |
| Engine | 15 deterministic Python tests passed, including status classification, corrupt snapshot rejection and pipe closure on parent loss. The stock CPython 3.12.14 Linux build loaded 396 compatible sites, including 12 Quick sites, without Python on PATH. A synthetic single-site GitHub lookup returned not found and completed with certificate verification enabled. |
| Native host | Seven Rust tests, Clippy and formatting passed. The Linux RC Debian payload displayed Search and read the complete catalog. Closing its verification window before startup completed produced exit code 1. The host and engine now use a liveness pipe so closing the host during a search terminates the worker. |
| Functional scope | Public handle discovery, progressive results, cancellation, native HTTPS opening, exports and opt-in local history. An inconclusive result can represent a real profile whose page lacks enough evidence to confirm a match. |
| Installer verification | The `0.1.0-rc.1` changes add a test-only launch flag for the shipped GUI, enabled explicitly by the caller. A successful exit requires the webview to render Search and load the native catalog. The matrix checks individual installer hashes before artifact upload. |
| Pull request | Git push works. An HTTPS CONNECT to api.github.com returned HTTP 403 from the cloud proxy. A restricted-network draft adds this single host. Manual draft PR creation is available through the [branch comparison](https://github.com/ish4ra/HuntWick/compare/main...feat/phase-1-desktop-mvp?expand=1). |

Keep the RC version until final platform results and remaining interactive acceptance checks are recorded. The stable version, merge and publication await review.

Native CSV, HTML and JSON saves exposed a missing timestamp in CSV. Commit `43749cd` appends the original UTC start time to each CSV record. A regression test failed on the prior implementation and passed after the fix. New installer verification must include this commit.

The Windows test harness at `a47935f` failed before launching the installed desktop because it indexed a copied environment dictionary with mixed-case `SystemRoot`. Commit `6cf7c32` normalizes Windows keys and supplies only System32 and the Windows root on PATH. A focused regression checks three casings, preservation of OS settings, and removal of inherited Python settings. The [corrected RC run](https://github.com/ish4ra/HuntWick/actions/runs/45294603221) is the acceptance run for this fix.

## Final RC.1 result

All four jobs passed in [run 45294603221](https://github.com/ish4ra/HuntWick/actions/runs/45294603221). The corrected Windows harness launched the installed desktop. Apple Silicon completed successfully in this run. Intel macOS and Linux also passed. All four archives were uploaded after verification of the five installer checksums. See the [RC archive links and digests](release-checklist.md#verified-release-candidate).

The [Linux interactive acceptance report](desktop-acceptance.md) distinguishes installed-RC tests from prior native sessions. The Linux AppImage separately launched through AppRun in extract-and-run mode and completed the GUI handshake with the OS graphics library available. Windows and macOS installer dialogs, default-browser handoff, native export dialogs and unsigned-install prompts still warrant interactive checks on representative user machines. The candidate is ready for approval review. Packaging remains at 0.1.0-rc.1.

### November 24 promotion gate

The RC installer matrix and Linux desktop evidence stand. A live Found result and public URL comparison still require an explicitly authorized account. Known blocked, challenge, timeout and ambiguous cases are covered by deterministic engine tests. Use the [owner sign-off checklist and draft release notes](release-checklist.md#owner-sign-off-and-stable-promotion) before the version change. Web Edition is the next planned milestone; its branch and deployment are future work.

The previously pending owner-authorized GitHub positive test passed on November 24. See the [recorded engine result](desktop-acceptance.md#authorized-positive-match--november-24). Desktop remains at RC.1 for owner device checks and release approval.

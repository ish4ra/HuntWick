# HuntWick v0.1.0 development status

## November 23 checkpoint

The feature branch is `feat/phase-1-desktop-mvp`. Commit `83c76a974313a58ce09aa41a1df46135b3308c5a` is the first remote checkpoint containing the frontend, Tauri host, Sherlock adapter, frozen-runtime recipe, site snapshot and installer workflows together. Development packages retain the alpha version pending platform acceptance.

| Area | Verification at this checkpoint |
| --- | --- |
| Frontend | ESLint, TypeScript, Vite production build and 34 Vitest cases passed. Browser checks covered navigation at two viewport sizes, filters, theme and history controls, and clipboard actions. |
| Native host | Linux debug executable built. Six Rust tests passed, including launching the frozen catalog and terminating a child process. Formatting and Clippy passed. |
| Sherlock | 14 deterministic Python tests passed. The frozen Linux executable loaded 396 compatible sites, including 12 Quick sites, and completed an offline search without Python on PATH. |
| UI screenshot | README shows the actual browser-rendered preview. Native search and file dialogs require the Tauri host. |
| GitHub CI | The complete host triggered [CI run 45149535174](https://github.com/ish4ra/HuntWick/actions/runs/45149535174). Installer acceptance requires the results for each matrix job. |
| Pull request | Git pushes work. The cloud proxy rejects HTTPS CONNECT to api.github.com with HTTP 403, before GitHub can authenticate the request. The [branch comparison](https://github.com/ish4ra/HuntWick/compare/main...feat/phase-1-desktop-mvp?expand=1) opens the manual draft-PR flow. |

## Remaining acceptance work

1. Verify Linux desktop startup, search, shutdown and native save behavior against the frozen engine. Record live versus fixture results separately.
2. Validate local Linux packages and inspect all four native CI jobs and their installer artifacts. Inspect the packaged engine from inside each installer. Preserve failing job details for any unavailable platform.
3. Finish parent-process-loss handling and validate the final sidecar inside the packages. Verify checksums, version consistency, and install/launch on clean target systems before promoting the version.
4. Keep the development branch open for review. Merge and publication require separate approval.

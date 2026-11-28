# RC.4 desktop acceptance

Production used commit `7d203a5aa40d7338e3a2d3857a777f00ab4b91f8`. All four installer jobs passed installed startup and packaged-engine checks. Each re-downloaded its uploaded archive and checked its SHA256. All four reported the RC.3 public-key fingerprint `cd307eeee71b7a46e73fbf139469c5f087f57839ba5eba90e40782eeeb341669`. [Production verification](https://github.com/ish4ra/HuntWick/actions/runs/45641860559) · [Desktop integration](https://github.com/ish4ra/HuntWick/actions/runs/45641810868)

Sign in to GitHub to download. Preserve these ZIPs before their 90-day retention expires.

| Download | Archive SHA256 |
| --- | --- |
| [Apple Silicon DMG](https://github.com/ish4ra/HuntWick/actions/runs/45641860559/artifacts/15036421995) | `4086715e3fb9ee865ccef8d3606c143ffe8609228e10020cccf277ea35a252e2` |
| [Intel macOS DMG](https://github.com/ish4ra/HuntWick/actions/runs/45641860559/artifacts/15037577044) | `6bbeefd63ced5be320be585845171dc346dfa58c8ced8f5612b686987566cb2f` |
| [Windows x64 NSIS](https://github.com/ish4ra/HuntWick/actions/runs/45641860559/artifacts/15035873083) | `2088fa78581336a1a66949be80df8feb07f484cc2b0b1998b173e5b32d887480` |
| [Linux x64 DEB and AppImage](https://github.com/ish4ra/HuntWick/actions/runs/45641860559/artifacts/15037460443) | `fcdb9e9a49d9f6e6e639a3c6b5b6eb4da439fadb99174d39ed84de3776a75af0` |
| [Offline promotion files](https://github.com/ish4ra/HuntWick/actions/runs/45641860559/artifacts/15038015297) | `7d0188d058ad255b2f2afbf070baa61c09de2477cacf42cba699cdc7aecc9e04` |

The production verification job checked the signed version and signature of each updater payload, compared each platform JSON entry with its versioned release URL and signature file, and verified the combined SHA256SUMS. It assembled the offline latest.json for windows-x86_64 (NSIS), darwin-aarch64 and darwin-x86_64 (app.tar.gz), and linux-x86_64 (AppImage). The promotion ZIP contains that manifest, SHA256SUMS and candidate.json with the source and run. [Verification job](https://github.com/ish4ra/HuntWick/actions/runs/45641860559/job/139313801086) · [Verification script](../scripts/prepare_candidate.py)

Web CI passed on `ca6234dee9095d4a3ee55ad1eb48ee6998086be0`, including authenticated Chromium search, CSV download, radar and audio assertions under the production CSP. The integration change after packaging affects only the browser smoke test and documentation. The application, engine and installer inputs match the production source. [Corrected Web CI](https://github.com/ish4ra/HuntWick/actions/runs/45723791656)

Audio previews · [Scan](rc4-media/scan.wav) · [Verified](rc4-media/verified.wav) · [Provider](rc4-media/provider.wav) · [Possible](rc4-media/possible.wav) · [Conflict](rc4-media/conflict.wav)

## Search measurements

The owner reported 396 RC.3 checks in 584 seconds, with three Found, 125 Not Found, 85 Blocked, 130 Timed Out, 43 Inconclusive and ten Error. Of 25 upstream claims on RC.3’s modified transport, 22 went outside the ordinary match view. Those figures are aggregate owner observations. The sum of active worker times is distinct from elapsed search time.

A synthetic two-site cloud run queried GitHub and GitLab sequentially by engine, with concurrency two, a five-second timeout and the same manifest, name and network. Stock was the unmodified Sherlock CLI. All three observed GitHub HTTP 404 and GitLab HTTP 200 with an empty user list. Stock and RC.4 both reported Available on both sites. There were zero positive results, errors or timeouts on this sample. The CLI includes startup and its update check.

| Source run | Wall time | First streamed outcome | Check duration, median / maximum | Sampled peak RSS, process tree | Sampled CPU time |
| --- | ---: | ---: | ---: | ---: | ---: |
| RC.3 | 4.66 s | 1.85 s | 2.54 / 3.88 s | 82.5 MiB | 0.86 s |
| Stock 0.16.2 | 3.91 s | CLI CSV at completion | See upstream CSV for header timing | 80.7 MiB | 0.63 s |
| RC.4 Original | 4.32 s | 1.20 s | 2.54 / 4.03 s | 138.7 MiB | 1.04 s |

A loopback proxy sent its CONNECT response one byte every 120 ms. With the same one-second timeout, concurrency two and three platforms, RC.3 took 7.23 s and returned three connection errors after 3.25–3.26 s per check. RC.4 took 2.81 s and returned three timeouts after 1.12–1.19 s, including worker startup. The network budget starts at dispatch to a ready worker and includes DNS, connection, redirects and body reads. Process startup and queue wait are separate costs. The optional retry grants one further attempt for a transient failure. It skips explicit denials.

In a separate loopback cancellation check, closing the native parent pipe while the frozen engine was waiting for a proxy response stopped the engine and its single active HTTP worker in 7 ms. This is one Linux measurement. The native Linux RC.4 window also launched and loaded the bundled catalog. [Native desktop](rc4-media/desktop.png) · [Desktop radar in browser](rc4-media/web-desktop.png) · [Mobile radar](rc4-media/web-mobile.png) · [Software updates, dark](rc4-media/updates-dark.png) · [Software updates, light](rc4-media/updates-light.png)

A local HTTP fixture compared the actual CLI’s requests and CSV verdicts with the desktop provider. Both issued two HEADs and one GET. Both reported Claimed for a generic HTTP 200, Available for a 404 and Claimed for a message-based 403. RC.4 retained both claims in the ordinary list, labeled the denial as conflicting evidence, and counted zero independently verified profiles. Enhanced API fixtures exercise explicit positive, negative, mismatched identity, rate-limit and redirect cases. Positive fixtures do not establish the accuracy of live sites.

A separate GitHub-only check of an authorized positive account returned Claimed from stock Sherlock. The local frozen RC.4 Original and Enhanced runs reported connection failures. Positive-match acceptance for the packaged candidate remains open.

## Owner acceptance and publication gates

1. Keep the installed production-key RC.3 and record a recognizable theme and one consented history entry. Retain its verified installer for recovery.
2. After separate approval, download the four RC.4 ZIPs, verify their archive digests and included installer manifests, and verify native signatures with the recorded permanent public key. Extract the promotion ZIP and check its source SHA and run ID in candidate.json. Use its four-target latest.json and verify the extracted payloads against its SHA256SUMS. Attach those same assets to the RC.4 prerelease, verify its URLs, then publish the preview feed last. Dispatching a fresh build produces different bytes. [Exact-byte promotion procedure](production-updater.md#4-prove-rc3--rc4-on-the-mac)
3. On RC.3, check stable first. Then check prereleases, accept RC.4, verify restart, version, history, preferences and bundled catalog. Repeat on representative Windows hardware. Listen to the optional cues with output enabled. Record native dialogs, the radar and cancellation behavior.
4. Repeat the owner's authorized Full search on the same network with the same handle, scope, timeout and concurrency. Compare original verdicts, conflict counts, independently verified profiles, time to first match, total elapsed time and per-site timings. Use the privacy-safe diagnostics export. Confirm selected native APIs with accounts you are authorized to test. Keep identifiers and exports local. The 130 owner timeouts and overall recall still need this comparison.

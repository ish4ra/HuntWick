# RC.6 desktop quality candidate

Development starts at the published RC.5 documentation commit `78322d5`. Installers linked from the README and the production preview feed still deliver RC.5. The app, installer and README use the RC.5 artwork. [Current optical magnifier studies for owner review](branding-v3/README.md)

## What the four modes contribute

| Mode | Default Full | Full with adult sites | Contribution |
| --- | ---: | ---: | --- |
| Sherlock Original | 394 | 410 | Stock-compatible Sherlock requests and verdicts |
| Enhanced Search | 396 | 412 | Eight native public lookups, including a matching account ID and username check on Scratch, plus remaining Sherlock rules |
| Maigret | 4,186 | 4,187 | Separately selectable rules from Maigret 0.6.7, including additional coding, creative and community profiles |
| Deep Search | 4,552 | 4,569 | Union by normalized profile, complementary checks, and per-provider agreement or disagreement |

Deep Search schedules Quick and native profiles first in large selections. A transient transport failure can leave time for another method. Identical failed requests are cached per profile for that attempt. Denials still stop the fallback. The result row exposes source verdicts even when they disagree. Partial coverage or an inaccessible service can still prevent a definitive outcome.

## Live comparison

The built React console used fixture desktop IPC to invoke the actual Python adapter. Each of the four selectors submitted a search for each of two requested public test handles against the same 11-platform selection, intersected with engine eligibility. The selection covered developer, gaming and creative sites with adult inclusion off. Three workers, five-second timeout, and the same cloud network were used throughout. Both handles yielded the following aggregate counts. The report omits account links and individual results.

| Engine | Checked | Independently verified | Provider match | Negative | Error |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sherlock Original | 7 | 0 | 1 | 2 | 4 |
| Enhanced Search | 9 | 1 | 0 | 3 | 5 |
| Maigret | 8 | 0 | 1 | 2 | 5 |
| Deep Search | 11 | 1 | 0 | 3 | 7 |

Deep checked four more platforms than Sherlock and two more than Enhanced. Each mode returned one visible candidate per handle. These runs establish routing and differences in evidence, but yielded **zero additional live matches** for Deep. The synthetic regression separately exercises a complementary provider recovering a match after a connection failure. No owner Full Search benchmark was performed.

## Full Search routing check

The built desktop interface submitted its default Full selection through fixture IPC to the Python adapter. A local transport returned fixture responses for the pinned rules, with outbound connections disabled. Codementor supplied a positive page on a Maigret-only route. The adult-enabled run also supplied a positive Meendo response.

| Deep Search selection | Requested profiles | Distinct result rows | Source verdicts | Fixture matches visible in Balanced |
| --- | ---: | ---: | ---: | --- |
| Adult sites off | 4,552 | 4,552 | 4,588 | Codementor |
| Adult sites on | 4,569 | 4,569 | 4,605 | Codementor and Meendo |

Both runs reached Complete. The returned platform names matched the submitted selection exactly, and every row carried at least one source verdict. The extra verdicts belong to overlapping provider rules. This check covers scheduling, aggregation and rendering across the whole pool. The live comparison above measures what external sites actually returned.

## Adult-profile coverage

Desktop starts with adult sites excluded and preserves existing choices on upgrade. Turning on the labeled switch explicitly enables the category and saves the setting. Both Search and Settings read the same state. Full includes all eligible enabled sites. Quick remains curated. Balanced shows match candidates. All results includes negatives, denials and errors.

Meendo now has an opt-in Maigret profile route in Maigret and Deep. Erome is available through Sherlock Original, Enhanced and Deep with adult inclusion enabled. The added tests check catalog filtering, engine routing, consent persistence and opt-out.

SpankBang has no rule in either pinned engine database or the reviewed WhatsMyName snapshot. Two third-party catalogs suggest different paths, `/profile/{username}` and `/p/{username}`. Neither entry supplies a verified positive/negative detection rule. Anonymous HEAD probes using a synthetic absent handle were denied during proxy CONNECT (403) on both routes; the origin returned no response. The platform is listed as unavailable. [Tookie catalog](https://github.com/Alfredredbird/tookie-osint/blob/228182a0f1a8b2f034d233556f6c80e405c21a66/sites/sites.json) · [Aliens Eye catalog](https://github.com/arxhr007/Aliens_eye/blob/932d751bfdad48150e432c6fc5b47f48c249a794/src/aliens_eye/data/sites.json)

## Desktop evidence

The Chromium checks exercised the actual sidecar from the built UI, checked the switch across reload and opt-out, and checked horizontal overflow at 1280×820 and 760×540. The compact results image uses synthetic events to show pacing, logos and layout. Rate and estimated remaining time use completed platform checks and elapsed time, including startup. For runs under 500 platforms, estimates start after three checks and three seconds. Larger runs show checked and pending counts while collecting at least 20 checks and 15 seconds of timing data. The estimate uses the whole-run average because the first batch prioritizes quick sites.

The radar’s single-result caption was removed. In the results list, Ko-fi (catalog name `kofi`), MyAnimeList, Patreon and VirusTotal use bundled icons. The later icon audit also added Behance, Kaggle, Last.fm, npm, SoundCloud and Vimeo. A built-UI fixture verified that all ten named provider rows used the expected local SVGs. Platforms without a mapped icon use the globe fallback.

[Normal window](rc6-media/normal.png) · [Minimum window](rc6-media/compact.png) · [Compact search console](rc6-media/compact-console.png) · [Compact results and pace](rc6-media/compact-results.png)

## Candidate verification

The first four-target build passed on Windows and both Mac architectures. On Linux, the upgrade harness inserted a TypeScript import ahead of the disposable older client's Vite type directive. Commit `81d0961` preserved the directive at the top of that file. The Linux-only rerun passed the private-feed signed AppImage upgrade, compared the installed bytes, relaunched RC.6 and checked the saved theme and history. [Initial matrix](https://github.com/ish4ra/HuntWick/actions/runs/45859587461) · [Linux rerun](https://github.com/ish4ra/HuntWick/actions/runs/45861322662)

On the restored-artwork build, nine web service tests passed locally. Authenticated Chromium checks exercised the shared search UI, CSV export, accessible radar blips, local icons and sound controls against a loopback web service.

All four targets passed for `f97a6dfcd9b8cf7556c10347001446cd0a103b18`. CI launched the desktop and checked the bundled engine on Windows, on both mounted Mac DMGs and on Linux. Linux also repeated the private signed AppImage upgrade. Each job verified its staged installers and uploaded archive digest. These archives use disposable CI updater keys and are available for manual owner testing. Published preview installs continue to receive RC.5. [Final desktop CI](https://github.com/ish4ra/HuntWick/actions/runs/45869171776)

| Manual test archive | Archive SHA-256 |
| --- | --- |
| [Apple Silicon Mac](https://github.com/ish4ra/HuntWick/actions/runs/45869171776/artifacts/15142881954) | `190ca03ccf67ee66309430050b9ec9d5fc97f25ac2cb5d376040138b0082175d` |
| [Intel Mac](https://github.com/ish4ra/HuntWick/actions/runs/45869171776/artifacts/15143332722) | `82aa6c7b0e95a052a983e29f1b354949452913aaab1ec78331ade818370de8a1` |
| [Windows x64](https://github.com/ish4ra/HuntWick/actions/runs/45869171776/artifacts/15143011871) | `d4746502d149790687b63f0bbdb42b8bf639c1509ed538fe2851ccef9652ca9f` |
| [Linux x64](https://github.com/ish4ra/HuntWick/actions/runs/45869171776/artifacts/15141953364) | `949a5c4e91eb4517b2b5f7221250db499abc665a33caa349c77e25c87bcd5bb7` |


## Long-search layout

Before a large run the console displays the configured batch size and per-attempt timeout. Results keep a Cancel search action alongside progress. The retry action starts a new search scoped to connection failures and timeouts.

The built desktop UI with synthetic IPC events was checked at 1280×820, 900×640 and 760×540. The engine controls and category switch fit at each width, and the radar circle fits inside its panel without clipping. In a 4,569-site fixture, four completed results left 4,565 pending while the estimate was calculating. [Wide console](rc6-media/full-console-1280.png) · [Intermediate console](rc6-media/full-console-900.png) · [Compact console](rc6-media/full-console-760.png) · [Compact progress and cancellation](rc6-media/full-progress.png)

## Production build inputs

After owner selection, apply the chosen application icon and wordmark to a single reviewed source commit. Use version `0.1.0-rc.6`, the production-candidate workflow and the RC.5 trusted public-key SHA-256 `cd307eeee71b7a46e73fbf139469c5f087f57839ba5eba90e40782eeeb341669`. The four test archives above use disposable keys.

Once the permanent-key matrix succeeds, pin its source commit, run ID, four archive IDs and digests, and the offline manifest archive in the existing exact-byte promotion workflow for RC.6. Preserve the active RC.5 manifest as a versioned rollback alongside the existing RC.4 asset. Rehearse read-only, then promote those same verified bytes to preview under owner authorization. [RC.5 promotion evidence](rc5-acceptance.md)

[Current search reliability measurements](rc6-search-quality.md) · [Updater in dark mode](rc6-media/updater-v2/dark/available.png) · [Updater in light mode](rc6-media/updater-v2/light/available.png)

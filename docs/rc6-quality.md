# RC.6 desktop quality candidate

Development starts at the published RC.5 documentation commit `78322d5`. Installers linked from the README and the production preview feed still deliver RC.5. [Candidate CI](https://github.com/ish4ra/HuntWick/actions/runs/45859587461)

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

## Adult-profile coverage

Desktop starts with adult sites excluded and preserves existing choices on upgrade. Turning on the labeled switch explicitly enables the category and saves the setting. Both Search and Settings read the same state. Full includes all eligible enabled sites. Quick remains curated. Balanced shows match candidates. All results includes negatives, denials and errors.

Meendo now has an opt-in Maigret profile route in Maigret and Deep. Erome is available through Sherlock Original, Enhanced and Deep with adult inclusion enabled. The added tests check catalog filtering, engine routing, consent persistence and opt-out.

SpankBang has no rule in either pinned engine database or the reviewed WhatsMyName snapshot. Two third-party catalogs suggest different paths, `/profile/{username}` and `/p/{username}`. Neither entry supplies a verified positive/negative detection rule. Anonymous HEAD probes using a synthetic absent handle were denied during proxy CONNECT (403) on both routes; the origin returned no response. The platform is listed as unavailable. [Tookie catalog](https://github.com/Alfredredbird/tookie-osint/blob/228182a0f1a8b2f034d233556f6c80e405c21a66/sites/sites.json) · [Aliens Eye catalog](https://github.com/arxhr007/Aliens_eye/blob/932d751bfdad48150e432c6fc5b47f48c249a794/src/aliens_eye/data/sites.json)

## Desktop evidence

The Chromium checks exercised the actual sidecar from the built UI, checked the switch across reload and opt-out, and checked horizontal overflow at 1280×820 and 760×540. The compact results image uses synthetic events to show pacing, logos and layout. Rate and estimated remaining time use completed platform checks and elapsed time, including startup. Estimates become visible after three checks and three seconds.

[Normal window](rc6-media/normal.png) · [Minimum window](rc6-media/compact.png) · [Compact search console](rc6-media/compact-console.png) · [Compact results and pace](rc6-media/compact-results.png)

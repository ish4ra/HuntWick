# Desktop catalog and CLI parity

Snapshot comparison at upstream c588d7c (November 2026) found 0 new names, 0 missing names and 0 changed entries against the bundled manifest. Latest official release tag remains v0.16.2. The v0.15.0 manifest contains these historical names absent under the same name today. Removal or renaming alone cannot establish whether a service still offers a permitted public lookup.

3dnews, 8tracks, Air Pilot Life, Alik.cz, Amino, AskFM, BLIP.fm, Bikemap, BodyBuilding, DeviantART, Fiverr, Freelance.habr, ICQ, KEAKR, Mapify, OGUsers, PepperIT, Shpock, TLDR Legal, TorrentGalaxy, babyRU, gfycat, iMGSRC.RU, mastodon.technology, queer.af, skyrock, wiki.vg

| Official behavior | HuntWick RC.2 |
|---|---|
| Single username and individual site selection | Search and platform selection |
| All compatible platforms / per-site timeout | Full Search and bounded timeout/concurrency |
| NSFW inclusion | Confirm desktop opt-in in Settings. Adult category is available for filtering. Resetting local data restores defaults. |
| Ignore false-positive exclusions | Opt-in experimental desktop checks, capped at Possible. Unsupported probes and unsafe methods remain excluded. |
| Claimed / available output | Eight outcomes and a diagnostic with the upstream verdict for completed HTTP probes |
| CSV / text / spreadsheet output | CSV, JSON, HTML and copy links. No native XLSX. |
| Mutable online or user-supplied manifest | Integrity-checked packaged snapshot only |
| Multi-username, permutations and proxy flags | One explicit handle per search. No bulk permutations or user-specified proxy controls. |
| Browser launch | User opens a selected HTTPS profile in the system browser |

At this snapshot the four desktop combinations yield 396 default, 414 with adult platforms, 437 with upstream-excluded platforms, and 456 with both. These are eligible checks, not verified availability claims. The hosted policy still permits only GitHub and GitLab.

An authorized single-site live comparison from the same cloud environment used GitHub, a 15-second timeout and the same definition. Official Sherlock reported Claimed; HuntWick returned Verified and the expected profile URL. This check does not identify causes of timeouts on the owner's network. For an owner-side comparison, repeat the same site selection on the same connection and export JSON locally. Completed probes report HTTP status, time to headers and total elapsed time. These timings combine DNS, connect and TLS. The transport distinguishes connection and read timeouts where the HTTP client exposes them. No profile-page contents or exception URLs are saved in diagnostics.

### Measuring an owner-side run

Select the same platforms, handle and timeout on the same network. Record concurrency, enabled catalog policies and start/end time separately. After completion choose **Export → Export diagnostics (no handle or URLs)**. The JSON contains the platform, outcome and recognized transport measurements only. The ordinary results JSON contains profile URLs and the handle. Review the platform names before sharing a diagnostic report. The hosted backend omits child diagnostic messages.

The headers timer measures the final HTTP exchange through response headers. Total time measures the worker's check, including earlier redirects and body processing. A DNS or connection failure can happen before either response headers or a Sherlock verdict is available. Resolver latency is not isolated. Checks run in a bounded pool; one slow platform can keep its worker occupied while completed checks stream to the UI.

A Linux loopback experiment used seven anonymous GETs per revision against the same 429 fixture. The fixture sent headers immediately and delayed its 512-byte body by 180 ms. Median completion fell from 183.2 ms to 1.9 ms when the adapter stopped reading denial bodies after the decisive status. This measures time saved on that response type. It does not estimate the duration of a live Full Search or attribute historical timeouts.

# RC.7 desktop coverage review

## What the owner’s run establishes

RC.6 completed 4,569 selected routes in about 52 minutes. The owner reported 14 provider matches, three verified matches, 2,082 timeouts, 411 blocked and 143 errors. Two nested Maigret match claims overlapped with other sources. No unique final match was attributed to Maigret in this run. The earlier RC.4 and RC.5 runs used different conditions. These measurements cannot establish recall or attribute all timeouts to one cause.

## Source comparison

The comparison uses the RC.6 desktop catalog with both optional categories enabled (4,612 distinct routes). For each external definition, compare the display/profile template first, using HuntWick’s host and path normalization and the same username placeholder. If that fails, compare punctuation-insensitive names or exact hostnames. A host/name overlap can represent different routes. An unmatched definition is a review lead, which can include stale sites, registration probes, subdomains and mirrors.

| Source | Available data and overlap | Decision |
| --- | --- | --- |
| [WhatsMyName final snapshot](https://github.com/WebBreacher/WhatsMyName/tree/abcb19d6809f0e963e353819c571133b45b6a106) | Archived in November 2026. Of 691 free website definitions, 202 matched a profile route, 43 more matched by name or host and 446 had neither match. Its JSON explicitly licenses the data CC BY-SA 4.0. | The response codes and positive/negative text markers need ongoing platform-specific validation. Imported adaptations would need attribution and share-alike terms. Used one lead, iNaturalist, to write an independent public-API lookup. No dataset rows redistributed. |
| [Blackbird](https://github.com/antoniaci/blackbird/tree/471ef970b4cd45378de1270c1b2b06687aa158b7) | Active repository. Its username loader downloads the same WhatsMyName database. Six local metadata definitions enrich responses. Email definitions concern a separate identifier. | Zero additional bundled rules. Its repository has CC BY-NC-SA 4.0 in .github/LICENSE and GPLv3 in docs/LICENSE. Neither establishes a new license for the fetched dataset. Adding its Python HTTP, reporting and metadata dependencies would duplicate the main check path. |
| [Enola](https://github.com/TheYahya/enola/tree/2bd8f923db674acfd8726ea9147000018dc86d1e) | Unarchived, last push July 2026. Its free data.json has 481 site definitions, 457 matching a route, two more matching by name or host and 22 unmatched. | Zero independently validated additions. Uses Sherlock-style status/message rules and a Go runtime. The README licenses the software under MIT. The database has no separate license declaration, and its provenance overlaps Sherlock. |
| [Namecheckers list](https://github.com/soxoj/osint-namecheckers-list/tree/8ebe939f5759b8b5e955ef22ce73014536efd5e2) | Maintained MIT directory of tools and services. Zero executable website definitions. | Research index. Each linked database has its own terms and quality requirements. |
| [Sherlock and Maigret provenance](../engine/notices/Provenance.md) | Both upstream repositories remain active. Pinned MIT packages and reviewed snapshots supply 481 Sherlock definitions and 11,071 upstream Maigret entries, of which 10,335 are upstream-enabled and 4,188 pass the bundled compiler. | Keep the existing runtimes, restrictions and route deduplication. Individual forum and development instances account for much of the catalog. A selected site can still be unreachable. |

The new iNaturalist route uses the service’s optional-authentication public v2 lookup and requests only login and ID. An exact login plus a positive integer identifier is required. Mismatched and ambiguous responses remain inconclusive. Synthetic positive, negative and denial tests pass. No live coverage increase has been measured. [Official API controller](https://github.com/inaturalist/iNaturalistAPI/blob/9f9738d69e083cab8e55d2da783312a32e83b512/lib/controllers/v2/users_controller.js)

## Instance-local identities

The inspected RC.6 request plans for mastodon.social and mastodon.online already issued GET requests to the instance’s account lookup. Their distinct hosts survive route deduplication. The old Maigret rules evaluated status and followed redirects. On mastodon.social, a preceding Sherlock block could stop Deep before the account lookup. Balanced includes provider claims and verified matches. The owner’s original per-site responses are unavailable. Independent queries to both public APIs failed during proxy CONNECT with HTTP 403, before either origin responded.

RC.7 uses the pinned account lookup before a complementary page check. Mastodon evidence requires a local acct, matching username, ID and instance profile URL. Supported Lemmy v3 routes require a matching name, local person, numeric ID and matching actor URL. A generic page, cross-instance actor, redirect or malformed response leaves identity unknown. A missing API or incompatible server version may also prevent verification. [Mastodon lookup](https://docs.joinmastodon.org/methods/accounts/#lookup) · [Lemmy API](https://join-lemmy.org/api/)

For installed acceptance, select Deep and Full. Enter a qualified address for an account you control on mastodon.social, confirm one selected route and inspect the source detail in Results. Repeat on mastodon.online. Try a known-absent local handle, then compare Balanced and Diagnostics. Record counts, HTTP status and outcome locally. This test distinguishes an access failure from negative identity evidence without another full-catalog run.

## Candidate counts

| Full mode | Default | Adult enabled |
| --- | ---: | ---: |
| Sherlock Original | 394 | 410 |
| Enhanced (native and Sherlock) | 397 | 413 |
| Maigret (including identity checks on supported federated routes) | 4,186 | 4,187 |
| Deep (all sources, deduplicated) | 4,553 | 4,570 |

With adult and experimental enabled, Deep exposes 4,613 eligible routes before per-site exclusions. The desktop Advanced category selector explicitly narrows a search. All categories remains the default. The restricted Web Edition retains its own allowlist. SpankBang has no validated bundled route.

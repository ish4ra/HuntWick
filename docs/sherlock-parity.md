# Comparing HuntWick with Sherlock 0.16.2

Both use Sherlock's rule loader and per-site classifier. The upstream CLI can load its live manifest and exclusions; HuntWick verifies digests for a bundled snapshot. Its 481 named rules yield 396 desktop targets, including 12 Quick Search targets at this revision. Of the 396, Sherlock evaluates 298 by status code, 72 by response message and 26 by response URL. The UI counts the installed, enabled selection at runtime. [Snapshot provenance](../engine/notices/Provenance.md)

The adapter bounds concurrency, body reads and redirects and uses anonymous HTTPS GET requests. It examines the actual response after Sherlock finishes. A status-based claim can mean only that an endpoint returned HTTP 200. Requiring a matching profile URL and owner evidence reduces false positives. It can also miss real accounts on client-rendered pages, truncated documents, redirects or sites with unfamiliar metadata. The original dashboard added several distinct unsuccessful outcomes to its inconclusive count. An aggregate saved by itself cannot establish how many were genuine upstream leads.

| Evidence in the offline comparison | Official CSV | HuntWick |
| --- | --- | --- |
| Matching canonical link and explicit profile handle | Claimed | Verified |
| Matching canonical link and handle-led title | Claimed | Possible |
| Profile type and matching owner handle, absent canonical URL | Claimed | Possible |
| Generic page, echoed handle, search results or conflicting canonical URL | Claimed | Inconclusive |
| Login or challenge page, HTTP 200 | Claimed | Blocked |
| Explicit missing marker or HTTP 404 | Available | Not found |
| HTTP 429 / 503 | Available | Blocked / Error |

An HTTP timeout and a cancelled search have their own outcomes. A reported match describes a public username. Check account ownership separately. The fixture harness executes the official CLI and compares its CSV output with adapter events for the same documents. [Comparison fixtures](../engine/tests/test_parity.py)

## Mainstream services

YouTube checks owner metadata in channel data. TikTok checks the profile's user record and recognizes private, region-blocked and missing responses separately. These paths have deterministic regression coverage; current real-world coverage still needs authorized testing. [YouTube report](https://github.com/sherlock-project/sherlock/issues/2977) · [TikTok report](https://github.com/sherlock-project/sherlock/issues/1076)

Instagram and X specify third-party mirrors, Reddit is excluded upstream, and the snapshot has no Facebook rule. The platform directory explains each omission. Reconsider a direct rule after verifying permitted, anonymous responses for known positive, negative and restricted cases. [Instagram](https://github.com/sherlock-project/sherlock/issues/3227) · [X](https://github.com/sherlock-project/sherlock/issues/2317) · [Reddit](https://github.com/sherlock-project/sherlock/issues/3018) · [Facebook](https://github.com/sherlock-project/sherlock/issues/1965)

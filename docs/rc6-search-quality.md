# RC.6 desktop search reliability

Deep Search correctly identified one Maigret-only fixture profile and rejected a missing profile. Neither live request reached its origin. **Incremental live matches demonstrated on this network: zero.** The owner’s RC.4 and RC.5 totals do not contain per-request traces that could attribute the historical timeouts to individual causes.

## Ground truth and measurements

The two selected routes, the Rust Users Forum and Rust Internals, have pinned Maigret Discourse JSON definitions. Neither route appears in the desktop Sherlock selection. Each case ran through a fresh Python 3.12 desktop sidecar with Deep Search, one selected site, one worker, a five-second request budget and retries disabled. No account links or response bodies were retained.

| Case | Expected outcome | Observed outcome | First result | Total | Peak tree RSS |
| --- | --- | --- | ---: | ---: | ---: |
| Rust Users Forum, offline matching JSON | Present | Maigret provider match | 961 ms | 1,125 ms | 109.0 MiB |
| Rust Internals, offline JSON 404 | Absent | Maigret not found | 757 ms | 921 ms | 108.7 MiB |
| Rust Users Forum, live public Discourse tutorial bot | Present, origin unverified here | Proxy denied CONNECT | 961 ms | 1,125 ms | 129.5 MiB |
| Rust Internals, live randomized synthetic handle | Presumed absent, origin unverified here | Proxy denied CONNECT | 802 ms | 970 ms | 129.5 MiB |

Offline ground truth comprised one positive and one negative. Deep detected 1/1 expected positives through Maigret with zero false positives, false negatives or transport failures. Sherlock contributed no rule on either route. The fixture substituted only the transport and exercised pinned provider verdicts and desktop reconciliation. Additional regression cases use a generic HTML success and another user’s JSON. Both previously produced a candidate and now return inconclusive.

The live set comprised one expected positive and one presumed negative. There were zero candidates, zero false positive claims, two transport denials and zero definitive presence or absence classifications. Counting every missed expected positive gives one operational miss. Origin-confirmed false negatives and live recall cannot be measured from these two denials. A proxy response is recorded separately from origin HTTP. No alternate route or retry was used. [Discourse tutorial bot](https://blog.discourse.org/2017/08/who-is-discobot/) · [Rust Users Forum](https://users.rust-lang.org/) · [Rust Internals](https://internals.rust-lang.org/)

Timing starts at process launch. First result ends at the first result frame, total ends at process exit, and RSS is the highest sum sampled across the sidecar and its children at 5 ms intervals on Linux. Shared pages can appear in more than one process’s RSS. These are individual cold launches. Together the two sequential fixture searches took 2.046 s and the two live searches took 2.095 s. They do not predict a Full Search duration or memory peak. In a separate cancellation run, a loopback fixture held the active worker at CONNECT. Closing the desktop parent pipe stopped the sidecar and its observed worker in **6 ms**.

## Causes and changes

- A stalled first provider could consume the whole Deep profile deadline. Providers now share the remaining budget among pending methods, with unused time available to later methods. Worker acquisition and startup also consume the request deadline. The scheduler still admits only the selected number of concurrent profiles.
- A proxy CONNECT denial previously surfaced as a generic connection failure, which could trigger another method or an automatic retry. A loopback 403 now produces exactly one CONNECT and a blocked result, with no origin status. The worker distinguishes resolver, proxy, TLS, generic connection and timeout failures without sending the request URL or exception text to the UI.
- A JSON profile route returning a generic success document could yield a Maigret claim for any input. On the 1,216 default Maigret Discourse routes using the reviewed JSON path, a candidate now requires a matching username and integer user ID. Source evidence retains the original provider verdict. An unrecognized HTTP 400-class response remains inconclusive. Native APIs can still recognize a documented missing-profile response.
- For fully qualified Bluesky handles, Deep’s native API used the correct actor but both upstream templates appended the default domain again. Deep now asks for the exact actor once. A confirmed match requires the returned handle and DID. Original provider templates remain pinned in their standalone modes. [Bluesky getProfile schema](https://docs.bsky.app/docs/api/app-bsky-actor-get-profile)
- HTTP workers are reused. Each exchange still opens its own anonymous session. A large catalog spans many origins, and this sample did not establish a cross-origin connection-reuse benefit. Existing per-profile coalescing still handles equivalent requests. Stale hosts, upstream rules, body limits and remote latency can still prevent a conclusion. No Full Search was repeated.

## Platform availability

With upstream experimental exclusions left off, the catalog still reports 394 Sherlock, 396 Enhanced, 4,186 Maigret and 4,552 Deep profiles. With explicit adult inclusion those counts are 410, 412, 4,187 and 4,569. The toggle changes eligibility. Restricted sites and routes without a validated detection method can remain unavailable.

HLTV’s numeric community IDs cannot be derived from the supplied username with a verified anonymous method. Its catalog exclusion remains visible. osu! can return a same-origin numeric profile redirect, which supports a possible match. A verified API v2 username lookup requires authorization. The focused regressions check the expected redirect and rejection of an unrelated destination. The hosted catalog was untouched. [Prior platform investigation](provider-research.md) · [osu! API documentation](https://osu.ppy.sh/docs/index.html#get-user) · [HLTV terms](https://www.hltv.org/terms)

Run the desktop engine checks with `engine/.venv/bin/python -m unittest discover -s engine/tests`. The 39-test run passed, including denial handling, cold-start deadlines, complementary lookup recovery, exact-domain Bluesky requests, normalized Discourse responses and catalog eligibility.

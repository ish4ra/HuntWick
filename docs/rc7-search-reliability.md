# RC.7 desktop transport benchmark

In the owner's RC.6 Deep Full run, 2,082 of 4,569 completed routes timed out (45.6%). Another 411 were blocked and 143 ended in error. Completion counts include all three outcomes. The owner’s aggregate measurements do not identify where individual requests spent their deadlines. [Owner run and source coverage](rc7-coverage.md)

## Same-route comparison

The test runs a fresh Python 3.12 desktop sidecar, one supervised worker, Deep mode, a one-second per-platform deadline and no retries. Four bundled Discourse routes receive synthetic answers from a loopback-only TLS fixture. Two routes answer immediately. Two return a complete same-origin redirect header and delay the intermediate body past the deadline. Their destinations answer immediately. The signed certificate used by the fixture is trusted only by the benchmark subprocess. Both versions use identical routes, order, responses, concurrency and evidence requirements.

| Selected Maigret-only route | Fixture | RC.6 | Changed worker |
| --- | --- | --- | --- |
| MetaDiscourse | Direct, matching JSON identity | Provider match | Provider match |
| discourse.ubuntu.com | Direct, HTTP 404 | Not found | Not found |
| Rust-lang | Redirect to matching JSON identity | Timed out | Provider match |
| internals.rust-lang.org | Redirect to HTTP 404 | Timed out | Not found |

Each column had the same outcomes in three cold runs. Time from process launch to exit was **3,084 / 2,792 / 2,783 ms** at RC.6 integration checkpoint `5a90b20` and **1,112 / 968 / 984 ms** with the change. The median fell from 2,792 to 984 ms. Both versions contacted four initial routes. The changed worker reached the two redirect destinations and correctly classified both additional fixtures. There were zero false positive classifications. In a separate cold run, sampling the summed resident memory of the sidecar and its children every 10 ms on Linux gave peaks of 131.7 MiB before and 131.9 MiB after. Shared pages can count more than once.

RC.6 buffered each redirect body before following the Location header. A slow or oversized intermediate document could therefore prevent the provider from receiving the final response. When the calling rule follows redirects, the worker now closes the intermediate socket as soon as it receives the redirect headers. Each destination still passes through the existing HTTPS and origin checks. A rule that inspects the redirect itself retains the original response body. A separate regression covers Requests wrapping a streamed body read timeout as a connection error. The worker now reports that failure as timed out.

## Interpretation

The desktop scheduler admits up to the chosen concurrency. A selected route waiting for admission has no running profile deadline. Once admitted, Deep divides the remaining attempt budget across its pending provider methods. Acquiring and starting an HTTP worker use the active request budget. Worker processes are reusable, each exchange uses an anonymous session, and equivalent probes can share a response within one profile. The final response body is subject to the existing 512 KiB limit. No routes were removed to obtain the timing difference.

This fixture measures one specific timeout mechanism. It cannot determine its prevalence among the owner’s 2,082 timeouts or establish public-site recall, Full Search duration or peak memory on the owner’s device. Stale origins, access denials, slow origins and other transport failures still limit the expanded catalog. The benchmark contacts no public sites.

The policy regression also exercises four synthetic catalog entries under all four combinations of adult and upstream-excluded eligibility. It checks that Deep accepts every visible fixture route and rejects each hidden route before invoking its provider.

Run the engine suite and reproduce the three-run benchmark from the repository root with Python 3.12, the engine dependencies and OpenSSL available.

```sh
engine/.venv/bin/python -m unittest discover -s engine/tests
engine/.venv/bin/python engine/tests/test_redirect_transport.py --benchmark engine
```

The benchmark accepts another checkout's engine directory as its last argument for comparing the same fixture with RC.6.

# Linux desktop acceptance

The installed Debian release candidate completed a live search in the native Tauri window and saved results through the GTK file chooser. The tester used a synthetic username and selected two platforms. The checks below cover the observed application behavior on Debian 13 amd64.

## Installed candidate

| Item | Value |
| --- | --- |
| Debian archive | `HuntWick_0.1.0-rc.1_amd64.deb` |
| Archive SHA-256 | `7fb196a8706c797c5f30496fe29d2e62174b74ce1a5e1da9b75899ac4cf262ce` |
| Installed executable SHA-256 | `b523b5cbd4c0b92b5097399c65eae95cfe744d36e3903f2decb82c80087f695d` |
| Package manager status | `hunt-wick 0.1.0-rc.1 install ok installed` |

`dpkg` installed the package and required WebKit libraries under a private package root. A read-only mount exposed the installed paths to the desktop session. The tester launched `/usr/bin/huntwick` on an Xvfb display using a temporary user profile. Reinstalling the rebuilt candidate preserved the platform selection and history preference. This environment shares the host's Debian base packages.

## Observations

| Check | Observed result |
| --- | --- |
| First launch | The RC displayed **Desktop edition**, **Ready**, 12 Quick platforms and 396 Full platforms. The native screenshot shows the initial RC before the CSV timestamp fix. [Native workspace, 1320 × 930](screenshots/desktop.png) |
| Search scope and progress | The tester used the platform switches to enable GitHub and PyPi. Quick then showed one selected platform and Full showed two. In the rebuilt candidate, the Full progress bar reached one of two checked while the search was running. Both platforms ultimately reported `not_found`. |
| Export from the rebuilt candidate | The tester saved CSV, JSON and HTML through the native chooser, reopened each file and compared the rows. The two records agreed on username, platform, category, status, URL and message. Both CSV records also included the UTC start time from the JSON export and the locally saved run. |
| Cancellation and repeated searches | In an earlier native build, Quick completed a one-site run. Cancelling a two-site Full run returned the console to Ready, and the next Full run completed. |
| Window close during a search | With the first installed RC, the tester observed the running engine child and sent the native window close event. Both the desktop process and its engine child exited. The rebuilt RC reopened with the same test profile and completed another search. |
| Local history and appearance | A native session began with history off. After opting in, the tester reopened the app, saw two completed searches and one cancelled search, and opened a saved run. Switching from Dark to Light changed the visible workspace colors. |

Live platform responses can change. This Linux run checked two platforms and produced no confirmed matches. Positive-match accuracy and the other catalog entries need separate evidence. Interactive checks on Windows and macOS remain separate release tasks. [Release checklist](release-checklist.md)

## Authorized positive match — November 24

An explicitly authorized single-platform test with the frozen RC engine returned a verified match. The returned HTTPS URL resolved to the expected public profile. The test used concurrency 1, a 15-second timeout and certificate verification. Account identifiers are omitted.

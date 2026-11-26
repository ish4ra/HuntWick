# RC.5 acceptance and promotion

RC.5 builds on reviewed Desktop/Web integration `56ae14f`. The hosted service keeps its authenticated GitHub/GitLab allowlist. The expanded profile directory and adult-category preference belong to desktop.

| Snapshot or selection | Count |
| --- | ---: |
| Maigret 0.6.7 upstream definitions | 11,071 |
| Upstream enabled | 10,335 |
| Disabled upstream | 736 |
| Outside HuntWick's compiled eligible set, including disabled entries | 6,891 |
| Compiled Maigret definitions | 4,180 |
| Default Maigret platforms after policy and deduplication | 4,179 |
| Default Sherlock Original / Enhanced Search | 394 / 396 |
| Default Deep Search unique platforms | 4,550 |

Eligibility reflects rule review. Independent per-platform validation across the full catalog is incomplete. Newly included templates cover Discourse, Gitea, GitLab, Flarum, Mastodon and Lemmy instances. HLTV remains unavailable without a verified public username route.

## Verification evidence

- Source tests exercised original verdicts, conflict resolution, request reuse, catalog policy and bounded network workers. The frozen Linux binary returned Maigret Claimed and Available for two local TLS responses with certificate validation enabled and developer tools removed from PATH.
- The frozen Linux binary returned HTTP 200 and Maigret Claimed for GitHub's public octocat demo account. The search reported 812 ms for the platform check.
- A separate live Deep Search used one synthetic handle, GitHub, GitLab and Codewars, concurrency two and a four-second timeout. The first result appeared at 1.88 s and the engine finished at 2.16 s. All three platforms completed, with two negatives, one connection error, zero timeouts, zero blocked, zero provider matches and zero verified matches. Peak sampled aggregate process-tree RSS was 201 MiB. This includes shared pages in each process.
- Closing the host pipe during a deliberately stalled local connection stopped the frozen supervisor and its one active HTTP worker in 8 ms. This measures process cleanup separately from UI cancellation.
- A separate Bluesky synthetic check reported a connection failure after 209 ms. The owner-side RC.4 timeout has no established root cause. These small samples cannot estimate a 4,550-platform Full Search duration or the change from the owner's 206-second RC.4 run.
- Desktop dark and light screenshots and the selector animation show the built React interface in Chromium with desktop fixture IPC. They do not establish physical-device acceptance.

## Production candidate

Production source is `90124af0358f9868fb7be05fbec3b6a3ed0ec560`. The trusted updater public-key SHA-256 is `cd307eeee71b7a46e73fbf139469c5f087f57839ba5eba90e40782eeeb341669`. [Desktop CI](https://github.com/ish4ra/HuntWick/actions/runs/45776637308) · [Web CI](https://github.com/ish4ra/HuntWick/actions/runs/45776637334) · [Production artifacts and signed manifest](https://github.com/ish4ra/HuntWick/actions/runs/45776673295) · [Owner review](https://github.com/ish4ra/HuntWick/pull/1)

The pinned promotion workflow runs a read-only rehearsal on `verify/rc5`. Only the owner-approved push to `promote/rc5` enables publication. It rechecks artifact archive digests, unpacks in a fresh directory, verifies the updater signatures and version bindings, and compares regenerated files byte-for-byte. The preview step stages the new manifest and retains the previous RC.4 bytes as a rollback asset.

## Release gates

1. Verify the four production CI jobs, five installers, signed updater archives, public-key fingerprint, exact archive digests and offline preview manifest.
2. Obtain owner approval before running the pinned promotion workflow. Verify the public bytes and preview feed from GitHub Actions.
3. On the installed RC.4 Mac, update through Software updates, relaunch and verify version, preferences, history, four engine choices, consent, Full Search workload and cancellation.
4. Review the integration PR and approve merging the combined Desktop/Web source to main. A stable release requires separate owner acceptance and approval.

## Verified Actions archives

| Archive | Artifact ID | ZIP bytes | SHA-256 |
| --- | ---: | ---: | --- |
| huntwick-aarch64-apple-darwin | 15096732954 | 140,585,274 | `f8b25eb153252c0a673171ba716c512b48d376d470de374294a2c6726fd7cddb` |
| huntwick-x86_64-apple-darwin | 15097781527 | 148,968,300 | `acd427cee61d0a0d05d9cf858530e9fc3338dfca6f5e3fb319b484a2793e1f54` |
| huntwick-x86_64-pc-windows-msvc | 15095639813 | 51,485,680 | `8cfc5b9c0bfbe358f792a7b0ad0a3b37bb327ef67027b58875fc91031b183d77` |
| huntwick-x86_64-unknown-linux-gnu | 15096029102 | 298,641,591 | `af7436ae9d6897f8312a2d458366c809b1894f17aea29e22de3d7e7e20e6a56c` |
| promotion-files | 15097976094 | 2,324 | `e36ebc198658258ffe350d0fd3b54bd52cdd921e7814151ce691d9de2a303469` |

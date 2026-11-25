# RC.3 desktop candidate

The integrated source uses the approved Cut wordmark, Counter icon and version 0.1.0-rc.3. RC.3 is the manual installation for the permanent-key updater trial. The production workflow checks the installed version and embedded verification key on all four targets, validates native payload signatures and signed versions, checks installer manifests and downloads each uploaded ZIP to compare its SHA256.

Candidate downloads will be recorded here after the production matrix passes. Use a signed-in GitHub account for Actions downloads. [Candidate build runs](https://github.com/ish4ra/HuntWick/actions/workflows/ci.yml?query=branch%3Abuild%2Fproduction-candidate)

The owner will separately exercise RC.3 → RC.4 on macOS and Windows. The private Web Edition awaits deployment approval. [Installation and update acceptance](production-updater.md) · [Unsigned installation](packaging.md)

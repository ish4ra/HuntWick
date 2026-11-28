# RC.3 desktop acceptance

HuntWick **0.1.0-rc.3** was built from commit [`5a10eb06721406ea3c93c2b1ef5ac8c6f2558146`](https://github.com/ish4ra/HuntWick/commit/5a10eb06721406ea3c93c2b1ef5ac8c6f2558146) on `build/production-candidate`. All four production jobs passed. The combined source also passed the four-target integration matrix and the authenticated Web Docker and Chromium checks. [Production build](https://github.com/ish4ra/HuntWick/actions/runs/45585725283) · [Integration CI](https://github.com/ish4ra/HuntWick/actions/runs/45585681832) · [Web CI](https://github.com/ish4ra/HuntWick/actions/runs/45585681808)

## Downloads

Sign in to GitHub to download the ZIP for your system. Compare its SHA256 below before extracting. Each ZIP includes its installer manifest, native updater payload, signature and target metadata. The workflow requested 90-day artifact retention. Keep the four original ZIPs with this record before GitHub expires them.

| Platform | Actions download | ZIP SHA256 |
| --- | --- | --- |
| Apple Silicon macOS · DMG | [Download ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45585725283/artifacts/15009735870) | `80d1c5a55dc141660f6bbe5530899886bdc57e5028409aeb9049bde095662d7a` |
| Intel macOS · DMG | [Download ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45585725283/artifacts/15009602043) | `30f468d3be7ed99201418acc2a57b7b38e6a4d1b0c6772b4762e1bcf804baa78` |
| Windows x64 · NSIS | [Download ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45585725283/artifacts/15010075143) | `f991d4ad757856894701ac4709a166c59a5790a571705fa18da0d1fe1f143295` |
| Linux x64 · Debian and AppImage | [Download ZIP](https://github.com/ish4ra/HuntWick/actions/runs/45585725283/artifacts/15009211647) | `8913d45f48b8059a50e1e14cb2d51b2015eb2e9c2bb51565f739fc6f0a7d670a` |

## What passed

- Installed Windows NSIS, mounted Apple Silicon and Intel DMGs, and the installed Debian package launched their native desktop and rendered the Search form. Each reported success after loading its packaged catalog, matching the RC.3 version and comparing the updater's compiled verification key with the repository public key. The Linux job also extracted and exercised the AppImage engine.
- The bundled Sherlock engines ran with Python removed from the test environment. Each native update payload passed its Ed25519 signature and signed-version check. The signed update formats are NSIS on Windows, the native app archives on macOS and AppImage on Linux.
- All four build notices reported the same SHA256 of the trimmed public-key file: `cd307eeee71b7a46e73fbf139469c5f087f57839ba5eba90e40782eeeb341669`. Each job rehashed its staged installer files and downloaded its uploaded ZIP to verify the digest.
- Local verification passed 43 frontend, 22 engine, nine web service, eight Rust, four packaging and four signature tests. The native Linux and authenticated browser captures use the approved Cut wordmark and Counter icon. The web result screenshots use deterministic demonstration events. [Desktop dark](screenshots/desktop-rc3.png) · [Desktop light](screenshots/desktop-rc3-light.png) · [Web dark](screenshots/web-desktop.png) · [Web light](screenshots/web-light.png) · [Mobile](screenshots/web-mobile.png)

## Owner acceptance

1. On Apple Silicon, verify the ZIP with `shasum -a 256 <download.zip>`. After extraction run `shasum -a 256 -c SHA256SUMS-aarch64-apple-darwin.txt` inside the extracted folder. Quit HuntWick, mount the DMG, drag the app into Applications, eject the image and open the installed copy. Check **Settings → Installed version 0.1.0-rc.3**. The updater signature is independent of Apple notarization and Windows Authenticode. [Platform installation guidance](packaging.md)
2. Save a recognizable preference and an optional synthetic history entry. The RC.3 → RC.4 in-app upgrade, restart and data retention require representative macOS and Windows devices and separate approval for RC.4 and its preview feed. Debian uses manual updates. [Device acceptance procedure](production-updater.md)
3. Repeat the authorized search on the owner's network with the original settings. Assess Verified and Possible Match accuracy and compare the diagnostic counts with the earlier 121 timeouts in 9 min 45 s. [Diagnostics checklist](catalog-audit.md#measuring-an-owner-side-run)
4. Review the integrated source and approve the exact main-branch merge separately. Stable publication, Web deployment and DNS remain owner decisions. [Integration review](main-integration.md)

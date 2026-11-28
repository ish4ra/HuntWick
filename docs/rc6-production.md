# RC.6 production release

The initial matrix used source `a1b696fe6c96a0cc3ebfb1c744ce892a476aa4f7`. It has the same tree as the reviewed Pivot and package-verification commit `38529ec`. The release workflow targets Apple Silicon Mac, Intel Mac, Windows x64 and Linux x64. [Production checks and archives](https://github.com/ish4ra/HuntWick/actions/runs/45977057788) · [Web Edition checks](https://github.com/ish4ra/HuntWick/actions/runs/45977057770)

The production workflow checks the permanent updater public-key fingerprint `cd307eeee71b7a46e73fbf139469c5f087f57839ba5eba90e40782eeeb341669`. The private Linux upgrade test uses a disposable trust anchor and isolated preferences. Owner acceptance of the installed RC.5 Apple Silicon upgrade follows preview publication.

[Desktop dark](rc6-media/pivot/desktop-dark.png) · [Desktop light](rc6-media/pivot/desktop-light.png) · [Settings](rc6-media/pivot/settings.png) · [Web Edition](rc6-media/pivot/web-desktop.png) · [Owner acceptance](rc6-owner-acceptance.md)

The initial matrix stopped in verification and produced no release archives. The corrected source is `4c283babbd4e6a4874e8633701bfeade2690f718`. The packaged-engine smoke check now verifies the closed-proxy outcome and the complementary deadline test uses a controlled clock. The local frozen engine smoke check, all 39 engine tests and five script tests passed before the new matrix started. [Corrected production run](https://github.com/ish4ra/HuntWick/actions/runs/46053737732) · [Final-source Web CI](https://github.com/ish4ra/HuntWick/actions/runs/46053737578)

## Verified release archives

All four production jobs and final-source Web CI passed. GitHub Actions verified the permanent signatures, installed application checks and isolated AppImage upgrade. The owner-gated rehearsal checked the original archive bytes, the offline preview manifest and the pinned RC.4 and RC.5 rollback bytes. [Read-only rehearsal](https://github.com/ish4ra/HuntWick/actions/runs/46093674799)

| Actions archive | ID | SHA-256 |
| --- | ---: | --- |
| huntwick-aarch64-apple-darwin | 15225818008 | `4da1a8902b08d1b003f3158fc29e56ca2ab1db406cd92f9653ae8f75a1f5da37` |
| huntwick-x86_64-apple-darwin | 15226569453 | `19259e1941895a8f68026177d9ffb69600c31397832d27be4632c7d6b3ea10ba` |
| huntwick-x86_64-pc-windows-msvc | 15225444679 | `4e4cfd552102a6b1c55731726c02d9ac228175ae58fa7dfb31aa03707c57da1d` |
| huntwick-x86_64-unknown-linux-gnu | 15225299553 | `a7679a0fda5a65d13806375b7ba6e7e546a8e66ba2c4c2b701cbec2a750c23d8` |
| promotion-files | 15226294384 | `e992705bec75cf0d9c110ce2d04a887458a12aedf388e81e8d90b62e9338708a` |

Offline preview manifest SHA-256: `733351e014ca4e14ae7f1981f4fb1b681b9da1284065e77e4a2e298fae91559b`.

The four verified signature envelopes are recorded in the rehearsal annotations and in the platform entries of the offline manifest. All four production packaging jobs recorded the RC.5 permanent-key fingerprint shown above. The separate key verification job was skipped.

## Published preview

GitHub published the original production files as a prerelease, verified their public bytes, then activated the preview manifest. The release and active manifests are byte-identical. The stable manifest returned HTTP 404. [Publication workflow](https://github.com/ish4ra/HuntWick/actions/runs/46093777368) · [Public release](https://github.com/ish4ra/HuntWick/releases/tag/v0.1.0-rc.6) · [Active preview](https://github.com/ish4ra/HuntWick/releases/download/updates-preview/latest.json)

| Public file | SHA-256 |
| --- | --- |
| [HuntWick-0.1.0-rc.6-aarch64-apple-darwin.app.tar.gz](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-aarch64-apple-darwin.app.tar.gz) | `58d55bb8c58c091f1ba62cf1ecd97a5d8df058e4f3b451017f7d7070a3d4e72b` |
| [HuntWick-0.1.0-rc.6-aarch64-apple-darwin.app.tar.gz.sig](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-aarch64-apple-darwin.app.tar.gz.sig) | `c5990e5f3c5408b470d5aaae0b3b3fe77a202713d0cbfcd280248449581fb0f0` |
| [HuntWick-0.1.0-rc.6-aarch64-apple-darwin.dmg](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-aarch64-apple-darwin.dmg) | `5210dc18fab22cb5e3f33902f11db87e64572e43a55e099fd2a8f337c8dfc1b5` |
| [HuntWick-0.1.0-rc.6-x86_64-apple-darwin.app.tar.gz](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-x86_64-apple-darwin.app.tar.gz) | `3b9258cb3931c12cdd8053ab6b1ef3fbf77af3aeea5021cf34a754de2cf84786` |
| [HuntWick-0.1.0-rc.6-x86_64-apple-darwin.app.tar.gz.sig](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-x86_64-apple-darwin.app.tar.gz.sig) | `5394559daa5406f2ca6d8587c8fc8e9b5124b815b70371be67091231e3bdd2ad` |
| [HuntWick-0.1.0-rc.6-x86_64-apple-darwin.dmg](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-x86_64-apple-darwin.dmg) | `4a55d6ffea695558bead34b1d271ad9ead7743a91243539e20b1e0aa13f9ccde` |
| [HuntWick-0.1.0-rc.6-x86_64-pc-windows-msvc.exe](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-x86_64-pc-windows-msvc.exe) | `6841d8b3255f6aa80b0d6176f9dc2744fc6c375f2efb4284ab4d835de96b3fb0` |
| [HuntWick-0.1.0-rc.6-x86_64-pc-windows-msvc.exe.sig](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-x86_64-pc-windows-msvc.exe.sig) | `6c10bb1a21bf28271bcbf2182339a288264feacff7f3a94547a8e9900ab33d9a` |
| [HuntWick-0.1.0-rc.6-x86_64-unknown-linux-gnu.AppImage](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-x86_64-unknown-linux-gnu.AppImage) | `e6a0181486760b38d5fbec6d016be83f3ce6f4b7ba1c7b98e874e130a95eced4` |
| [HuntWick-0.1.0-rc.6-x86_64-unknown-linux-gnu.AppImage.sig](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-x86_64-unknown-linux-gnu.AppImage.sig) | `e57276e8588af38d490e97a2413e16d85510603963dfc432150a7f66d224bc32` |
| [HuntWick-0.1.0-rc.6-x86_64-unknown-linux-gnu.deb](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/HuntWick-0.1.0-rc.6-x86_64-unknown-linux-gnu.deb) | `9ec418845497e6d691c8d00eaff37c63a5aa4896ceb9fe99df27309b2e264acb` |
| [SHA256SUMS](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/SHA256SUMS) | `84c28e9c0d2915c46344d6d3edf829108bfdb3accacb46bc831caf787f55781f` |
| [latest.json](https://github.com/ish4ra/HuntWick/releases/download/v0.1.0-rc.6/latest.json) | `733351e014ca4e14ae7f1981f4fb1b681b9da1284065e77e4a2e298fae91559b` |

| Preview rollback | Verified SHA-256 |
| --- | --- |
| [RC.5](https://github.com/ish4ra/HuntWick/releases/download/updates-preview/latest-0.1.0-rc.5.json) | `26a150727f70e68ec5d6510e4f68a4e2362f43d103e7ef1bd1e5f8d33c26577a` |
| [RC.4](https://github.com/ish4ra/HuntWick/releases/download/updates-preview/latest-0.1.0-rc.4.json) | `98cdaa90f1fdef0ade2ff84d9d3489453f69022238b5597bbd1a33efaa3c37a4` |

## First stable release checklist

- [ ] Complete the [installed Apple Silicon RC.5 upgrade and acceptance checks](rc6-owner-acceptance.md). Record live search limitations and resolve any release-blocking defects.
- [ ] Obtain explicit owner approval for the stable transition, complete final PR #1 review and merge into main.
- [ ] Set app, package and updater metadata consistently to `0.1.0`. Run one permanent-key production matrix and Desktop and Web CI on the final source.
- [ ] Rehearse exact-byte promotion with the new stable artifacts. Verify embedded versions, checksums, signatures and that existing preview installations recognize `0.1.0` as a newer trusted update.
- [ ] Publish `v0.1.0`, verify every public download and signature, then activate the stable manifest. Verify both channel selections and retain prior releases and rollback manifests.
- [ ] Point README downloads at the verified stable files. Web deployment and DNS can be scheduled separately.

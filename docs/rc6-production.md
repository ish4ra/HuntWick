# RC.6 production candidate

The production source is `a1b696fe6c96a0cc3ebfb1c744ce892a476aa4f7`. It has the same tree as the reviewed Pivot and package-verification commit `38529ec`. The release workflow targets Apple Silicon Mac, Intel Mac, Windows x64 and Linux x64. [Production checks and archives](https://github.com/ish4ra/HuntWick/actions/runs/45977057788) · [Web Edition checks](https://github.com/ish4ra/HuntWick/actions/runs/45977057770)

The production workflow checks the permanent updater public-key fingerprint `cd307eeee71b7a46e73fbf139469c5f087f57839ba5eba90e40782eeeb341669`. The private Linux upgrade test uses a disposable trust anchor and isolated preferences. Owner acceptance of the installed RC.5 Apple Silicon upgrade follows preview publication.

[Desktop dark](rc6-media/pivot/desktop-dark.png) · [Desktop light](rc6-media/pivot/desktop-light.png) · [Settings](rc6-media/pivot/settings.png) · [Web Edition](rc6-media/pivot/web-desktop.png) · [Owner acceptance](rc6-owner-acceptance.md)

The initial matrix stopped in verification and produced no release archives. The corrected source is `4c283babbd4e6a4874e8633701bfeade2690f718`. The packaged-engine smoke check now verifies the closed-proxy outcome and the complementary deadline test uses a controlled clock. The local frozen engine smoke check, all 39 engine tests and five script tests passed before the new matrix started. [Corrected production run](https://github.com/ish4ra/HuntWick/actions/runs/46053737732) · [Final-source Web CI](https://github.com/ish4ra/HuntWick/actions/runs/46053737578)

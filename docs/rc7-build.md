# RC.7 production verification

The final installer source is `efd1ff538153ceb18309af7c05c5dd7d66990be5`. The clean-checkout build passed 76 frontend, 49 engine, five script, nine Web service and four updater-signature tests. Chromium exercised both color themes, the published notes, the preview notice and the explicit one-time opt-in. The installed application smoke test also decodes bundled Mastodon, Lemmy and Wattpad artwork before reporting success.

[Four-target production matrix](https://github.com/ish4ra/HuntWick/actions/runs/46143117478) · [Web CI](https://github.com/ish4ra/HuntWick/actions/runs/46143117444) · [Logo audit](platform-logos/README.md) · [Owner acceptance cases](rc7-coverage.md)

RC.6 is the active preview. Publication of RC.7 requires successful artifact verification, read-only rehearsal and explicit owner authorization.

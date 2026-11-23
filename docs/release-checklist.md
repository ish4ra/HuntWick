# v0.1.0 release acceptance

Use the commit and package version printed in the candidate's CI run. Record the OS version, CPU architecture, installer filename and digest with each result. The current evidence and outstanding checks live in [development status](DEVELOPMENT_STATUS.md).

1. Verify all four matrix jobs succeeded for the candidate. Download the four archives, compare each archive's SHA256 with the digest shown by GitHub, extract the archive, and verify each installer against its included SHA256 manifest.
2. Install on Windows x64, Apple Silicon macOS, Intel macOS, and Linux x64 using ordinary user privileges for launch. Exercise the Linux DEB and AppImage separately. Check the app icon, version, initial Search view and platform count. End users need no Python installation.
3. With history disabled, enable a single compatible site. Search for a synthetic handle or an account you control. Verify the total, checked count, individual status, and live updates. Confirm a second launch has no saved search. Enable history, complete another search, reopen the entry, then delete it.
4. In a bounded Full search, cancel during a request, start another search immediately, and close the window while busy. Verify the engine exits, then relaunch. Check that late results from the cancelled search do not appear in the new search.
5. Use table and card views, sorting, filters, copying and the default browser. Save CSV, JSON and HTML through the OS save dialog. Reopen each file and compare its statuses and URLs with the UI. Cancel the save dialog once, and check overwrite behavior on a temporary file.
6. Switch theme and density, restart, and verify preferences and history consent. Test clearing local data and restoring platform defaults. Distinguish access blocks and timeouts from confirmed matches using deterministic fixtures.
7. Review the MIT and dependency notices, unsigned installation instructions, and known limitations. Test the Windows minimum version and macOS security prompts on representative machines. Obtain explicit approval of final artifacts and version before merge or public release.

## Verified alpha packaging baseline

All four jobs for commit `4f8ae0c0c61a45e12d7f59e357f44700a15dcf55` passed. Each exercised the bundled engine from its installer payload. GitHub reports the following SHA256 values for **artifact archives**. Individual installer checksums are in each archive. [Build and artifact summary](https://github.com/ish4ra/HuntWick/actions/runs/45149732056)

| Target | Archive SHA256 | Download |
| --- | --- | --- |
| Windows x64 | `e8e9b0feb5e0133b635fa81540f850c91ae0a8f448cc388f4bd2d3c5abedc16a` | [NSIS](https://github.com/ish4ra/HuntWick/actions/runs/45149732056/artifacts/14807000253) |
| macOS ARM64 | `66dd03354e96c3fa7b4ea973ab576553775d3ea73594aa13d33b02726c55e125` | [DMG](https://github.com/ish4ra/HuntWick/actions/runs/45149732056/artifacts/14805667868) |
| macOS x64 | `9f4a46c1d1e1ec5ed99627f0ecc0a2184eed6eeec4a0c68fe2437b518d5021c6` | [DMG](https://github.com/ish4ra/HuntWick/actions/runs/45149732056/artifacts/14806113599) |
| Linux x64 | `321a71e5dfa05727337d9851cbdc1136b6a02b2da030cd67fc585d46df250fd1` | [DEB and AppImage](https://github.com/ish4ra/HuntWick/actions/runs/45149732056/artifacts/14806855697) |

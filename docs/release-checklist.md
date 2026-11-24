# v0.1.0 release acceptance

Use the commit and package version printed in the candidate's CI run. Record the OS version, CPU architecture, installer filename and digest with each result. The current evidence and outstanding checks live in [development status](DEVELOPMENT_STATUS.md).

1. Verify all four matrix jobs succeeded for the candidate. Download the four archives, compare each archive's SHA256 with the digest shown by GitHub, extract the archive, and verify each installer against its included SHA256 manifest.
2. Install on Windows x64, Apple Silicon macOS, Intel macOS, and Linux x64 using ordinary user privileges for launch. Exercise the Linux DEB and AppImage separately. Check the app icon, version, initial Search view and platform count. End users need no Python installation.
3. With history disabled, enable a single compatible site. Search for a synthetic handle or an account you control. Verify the total, checked count, individual status, and live updates. Confirm a second launch has no saved search. Enable history, complete another search, reopen the entry, then delete it.
4. In a bounded Full search, cancel during a request, start another search immediately, and close the window while busy. Verify the engine exits, then relaunch. Check that late results from the cancelled search do not appear in the new search.
5. Use table and card views, sorting, filters, copying and the default browser. Save CSV, JSON and HTML through the OS save dialog. Reopen each file and compare its statuses and URLs with the UI. Cancel the save dialog once, and check overwrite behavior on a temporary file.
6. Switch theme and density, restart, and verify preferences and history consent. Test clearing local data and restoring platform defaults. Distinguish access blocks and timeouts from confirmed matches using deterministic fixtures.
7. Review the MIT and dependency notices, unsigned installation instructions, and known limitations. Test the Windows minimum version and macOS security prompts on representative machines. Obtain explicit approval of final artifacts and version before merge or public release.

## Current RC.2 candidate

The four-platform matrix passed. Download the five candidate installers and review the updater evidence, archive digests and owner device checks. [RC.2 acceptance](rc2-acceptance.md)

## Verified release candidate

All four jobs passed at commit `6cf7c32d4c104cd2d77efa966cbe72610bacdc1f`. CI launched the installed Windows app, both macOS app bundles and the installed Debian app. Each completed the webview and native catalog handshake. CI rehashed all five installers against the staged manifests before upload. The SHA256 values below are GitHub's archive digests. Each archive also contains the individual installer manifest. [Corrected RC run](https://github.com/ish4ra/HuntWick/actions/runs/45294603221)

| RC.1 archive | Archive SHA256 |
| --- | --- |
| [huntwick-aarch64-apple-darwin](https://github.com/ish4ra/HuntWick/actions/runs/45294603221/artifacts/14876337739) | `f0a88510a9d0161ace5049ef35495f76e086fe45b69f7983f595bf0062b1d414` |
| [huntwick-x86_64-apple-darwin](https://github.com/ish4ra/HuntWick/actions/runs/45294603221/artifacts/14876781277) | `4996f14a27c0ad294e73e292c98f7246e9be0a5fe5880450a321d57b0588cbba` |
| [huntwick-x86_64-pc-windows-msvc](https://github.com/ish4ra/HuntWick/actions/runs/45294603221/artifacts/14877010845) | `cac1a17e8982b7ee9fd523abbd84076c767b9c3daa46bb7756a35588e16894e7` |
| [huntwick-x86_64-unknown-linux-gnu](https://github.com/ish4ra/HuntWick/actions/runs/45294603221/artifacts/14875922742) | `4ff302ec83f47027f4bf0326ad8e63d71d23b60bb2a01b7cd567986365766b9c` |

## Verified alpha packaging baseline

All four jobs for commit `4f8ae0c0c61a45e12d7f59e357f44700a15dcf55` passed. Each exercised the bundled engine from its installer payload. GitHub reports the following SHA256 values for **artifact archives**. Individual installer checksums are in each archive. [Build and artifact summary](https://github.com/ish4ra/HuntWick/actions/runs/45149732056)

| Target | Archive SHA256 | Download |
| --- | --- | --- |
| Windows x64 | `e8e9b0feb5e0133b635fa81540f850c91ae0a8f448cc388f4bd2d3c5abedc16a` | [NSIS](https://github.com/ish4ra/HuntWick/actions/runs/45149732056/artifacts/14807000253) |
| macOS ARM64 | `66dd03354e96c3fa7b4ea973ab576553775d3ea73594aa13d33b02726c55e125` | [DMG](https://github.com/ish4ra/HuntWick/actions/runs/45149732056/artifacts/14805667868) |
| macOS x64 | `9f4a46c1d1e1ec5ed99627f0ecc0a2184eed6eeec4a0c68fe2437b518d5021c6` | [DMG](https://github.com/ish4ra/HuntWick/actions/runs/45149732056/artifacts/14806113599) |
| Linux x64 | `321a71e5dfa05727337d9851cbdc1136b6a02b2da030cd67fc585d46df250fd1` | [DEB and AppImage](https://github.com/ish4ra/HuntWick/actions/runs/45149732056/artifacts/14806855697) |

## Owner sign-off and stable promotion

For the Windows and macOS interactive checks, use the corrected RC installers: [Windows NSIS](https://github.com/ish4ra/HuntWick/actions/runs/45294603221/artifacts/14877010845), [Apple Silicon DMG](https://github.com/ish4ra/HuntWick/actions/runs/45294603221/artifacts/14876337739), [Intel DMG](https://github.com/ish4ra/HuntWick/actions/runs/45294603221/artifacts/14876781277).

- On each target, verify the checksum, install using the [unsigned installation instructions](packaging.md), and launch from the applications menu. Record the OS, architecture, security prompt and displayed RC version.
- Enable only the authorized account's platform. Search its handle, confirm Found, open the result in the default browser, and compare the destination and displayed handle with the owner's expected public URL. Record the outcome and date. Keep unrelated accounts and private profile details out of the evidence.
- Exercise Cancel, Save and overwrite in the native export dialog using a temporary file. Reopen CSV, JSON and HTML, compare their records, and confirm the CSV search timestamp. Quit during a bounded search, then relaunch and check history consent and preferences.

After positive-match and owner sign-off, prepare a promotion commit setting version 0.1.0 in package.json, package-lock.json, the Tauri config, Cargo.toml, Cargo.lock and the displayed UI version. Finalize the README and CHANGELOG with the approved release date and limitations. Run the full installer matrix on that commit and verify the five stable-version filenames and their checksums. Obtain explicit merge approval. After merge, confirm main contains the approved release tree; with explicit publication approval, dispatch the Release workflow from main with channel stable. It rebuilds all four targets, verifies the manifests and publishes v0.1.0 with five installers and SHA256SUMS. Verify the public assets and hashes against the publication run.

### Draft release notes for owner review

HuntWick brings Sherlock-powered public username discovery to Windows, macOS and Linux with a bundled runtime, progressive results, cancellable searches, local exports and optional history. The candidate ships with 396 compatible platforms and 12 Quick sites. A shared handle cannot establish account ownership. Site behavior can change, and ambiguous responses can remain inconclusive. Desktop installers are unsigned; see the platform instructions before installation.

# Permanent updater key and owner acceptance

Use RC.3 as the first installation that trusts the owner's permanent key. RC.2 was tested with disposable signing material. Plan one manual installation on the Mac, followed by an in-app move from RC.3 to RC.4. Production upgrades on macOS and Windows still require device evidence.

## Current signing evidence

The owner configured the permanent key locally. On November 25, GitHub Actions signed a fixed text fixture with the repository private key and password. An independent verifier checked its Ed25519 signature and the signed version `0.0.0` against the repository public key. Both steps passed. The job had read-only repository permissions and produced zero downloadable artifacts. This verifies the configured credentials. Installer signing and production device upgrades will be exercised with the approved RC.3 and RC.4. [Signing job](https://github.com/ish4ra/HuntWick/actions/runs/45549365080/job/138986565862)

The production candidate job requires an owner push on the designated build ref. The release job requires an owner dispatch on main or the desktop development ref. Both also check the initiating account on a rerun. Repository writers who can edit Actions workflows are part of the signing trust boundary. Restrict write access and protect signing workflow changes accordingly.

## 1. Generate the key once on the owner's Apple Silicon Mac

If you already created the permanent key pair, keep it and go to step 2. Otherwise open **Terminal** on the Mac and paste the block below. The downloaded tool is the official standalone Tauri CLI 2.12.6. Its archive digest is pinned to the value on the upstream release. macOS supplies the other commands. You can do this without a repository checkout, Node, Homebrew or Rust. [Official CLI download and digest](https://github.com/tauri-apps/tauri/releases/tag/tauri-cli-v2.12.6)

```sh
(
  set -eu
  umask 077
  unset CI
  keydir="$HOME/.huntwick-updater"
  mkdir -p "$keydir"
  cd "$(mktemp -d)"
  curl --fail --location --proto '=https' --retry 2 \
    'https://github.com/tauri-apps/tauri/releases/download/tauri-cli-v2.12.6/cargo-tauri-aarch64-apple-darwin.zip' -o signer.zip
  printf '%s  signer.zip\n' '1c71c48a9aea9616a857c92bab63bc9bce113e348929493ba0bbaa4d3f4ce4c3' | shasum -a 256 -c -
  unzip -q signer.zip cargo-tauri
  ./cargo-tauri signer generate -w "$keydir/huntwick.key"
)
```

At the signer's prompt, enter and confirm a unique, nonempty password saved in your password manager. The signer writes the encrypted private key to `~/.huntwick-updater/huntwick.key` and the public key to `huntwick.key.pub`. It refuses to overwrite an existing pair. Finder's **Go → Go to Folder** can open `~/.huntwick-updater`.

Back up both files on encrypted offline media and check that you can read the backup. Keep a separately recoverable copy of the password. Compare the public-key fingerprint below with the fingerprint in each production build's GitHub job summary. Save the fingerprint with your release records.

```sh
tr -d '\r\n' < "$HOME/.huntwick-updater/huntwick.key.pub" | shasum -a 256
```

GitHub secrets cannot be read back as a backup. Losing the private key or its password ends your ability to sign updates for installations that trust that pair. If the key is compromised, stop feed publication, remove its signing secrets and distribute a separately verified installer that embeds a new public key.

## 2. Save the three values in GitHub

On the Mac, use an owner/admin account for the repository. Choose **New repository variable** or **New repository secret** and paste the entire indicated value. If you chose a different key location, substitute that path. File contents go into GitHub, including the private file's encryption. Use your local clipboard only for this transfer, with clipboard history and cross-device sharing paused for secret values.

| Name | Where to save it | Value |
| --- | --- | --- |
| `UPDATER_PUBLIC_KEY` | [Actions variables](https://github.com/ish4ra/HuntWick/settings/variables/actions) | Copy with `pbcopy < "$HOME/.huntwick-updater/huntwick.key.pub"` |
| `UPDATER_PRIVATE_KEY` | [Actions secrets](https://github.com/ish4ra/HuntWick/settings/secrets/actions) | Copy with `pbcopy < "$HOME/.huntwick-updater/huntwick.key"` |
| `UPDATER_KEY_PASSWORD` | [Actions secrets](https://github.com/ish4ra/HuntWick/settings/secrets/actions) | Paste the password from your password manager |

After saving, clear the clipboard with `pbcopy < /dev/null`. Confirm only that all three names are configured. Keep secret values out of chat, issues, command lines and build logs.

## 3. Build RC.3 as Actions artifacts

The existing **Release** workflow builds and then publishes when dispatched. The **CI → Production-key candidate (artifacts only)** job has read access and ends with verified Actions downloads. Its trigger is a push of the reviewed development commit to the dedicated build ref. This works while `main` contains only the baseline README and has no manual-dispatch workflow. If the repository is public, people with artifact download access may be able to download a candidate.

1. Obtain the owner's wordmark choice, signing-setup confirmation and approval to build. Complete the selected identity across desktop, web and README, including the platform icons and static fallback. Validate those changes in their respective branches.
2. Set the desktop version to `0.1.0-rc.3` in package.json and its lockfile, the Tauri config, the Rust package and lockfile, and the displayed UI version. Update the changelog and candidate notes. Keep historical signed test fixtures bound to their original version.
3. In Codex Cloud, review the exact desktop commit on `feat/phase-1-desktop-mvp`, including its workflow and packaging code. Once authorized, run the block below with the **full approved SHA** entered for `candidate`. Use a commit eligible for CI (without a skip directive). Only maintainers authorized to sign should be able to update this build ref and production workflows.

```sh
(
  set -eu
  candidate='REPLACE_WITH_APPROVED_FULL_SHA'
  git fetch origin refs/heads/feat/phase-1-desktop-mvp
  test "$(git rev-parse FETCH_HEAD)" = "$candidate"
  git push origin "$candidate:refs/heads/build/production-candidate"
)
```

4. Check that the build-ref CI run shows that SHA and **Production-key candidate (artifacts only)**. This job passes `release-signing: true`. Missing public key, private key or password fails the build. The production public key supplies both the compiled Rust verifier and Tauri packaging configuration. Staging independently verifies each native payload's Ed25519 signature and signed version against that same public key. An incorrect key pair or password fails signing or verification. Ordinary CI uses a separate disposable-key path.
5. Require all four jobs to pass. Check the public-key fingerprints, all four ZIP digests, and the per-file SHA256 manifests. The five installers are Windows NSIS, Apple Silicon and Intel DMGs, Linux DEB and AppImage. Updater payloads are NSIS, two native `.app.tar.gz` archives and AppImage. Keep the matching signatures and the four platform JSON files with the tested bytes.
6. Download the verified Apple Silicon candidate ZIP, check it with `shasum -a 256`, extract it, then run `shasum -a 256 -c SHA256SUMS-aarch64-apple-darwin.txt` in the extracted directory. Quit HuntWick, mount the DMG, install it in **Applications**, eject the DMG and open the installed app. Confirm RC.3 in Settings. Updater signatures and macOS notarization serve different purposes. [Unsigned installation guidance](packaging.md)

## 4. Prove RC.3 → RC.4 on the Mac

1. In RC.3, select a recognizable appearance preference, enable local history if desired, and save one synthetic or owner-authorized search. Record its summary and the platform count locally.
2. Prepare and build a distinct `0.1.0-rc.4` from the desktop branch by the same artifact-only procedure. Require the same production public-key fingerprint on all four targets. Save the RC.4 installer and its verified checksums for recovery.
3. **Pause for explicit prerelease-publication approval.** Record the approved SHA, Actions run, ZIP digests and intended channel. For promotion of those exact bytes, download and verify the four ZIPs, then extract their contents together into `installers/` in a checkout at the approved RC.4 SHA. Run `python scripts/updater_assets.py manifest`. Combine the target manifests into `SHA256SUMS` and verify with `sha256sum --check --strict SHA256SUMS`. Verify the native payload signatures using the recorded production public key, and inspect the generated `latest.json` for RC.4, all four platform entries and their versioned GitHub URLs.
4. With that approval, create the **prerelease** `v0.1.0-rc.4` at the approved SHA. Attach the verified installers, native update archives, signatures, combined checksum manifest and `latest.json`. Check each referenced asset is present. Publish the same `latest.json` on the `updates-preview` prerelease feed **last**. The release workflow builds fresh bytes when dispatched, so exact-byte promotion uses the archived candidate files. The stable feed is reserved for an independently approved stable release.
5. In the installed RC.3, finish or cancel any active search. Open **Settings → Check stable**. RC.4 must never appear there (a missing stable feed can report an error). Select **Check prereleases**, confirm `0.1.0-rc.4`, then **Install 0.1.0-rc.4 and restart**. Record observed progress, verification or error text, automatic relaunch and the displayed version. Attempt a preview check again to confirm the same version is no longer offered.
6. Confirm preferences and saved results, load Platforms, run an authorized Quick Search with the bundled engine, and open a result. If installation failed, record the stage, verify the saved RC.4 DMG against its checksum and install it manually. Record recovery separately from in-app success. Repeat the installed-upgrade acceptance on Windows before claiming Windows production support. The DEB continues to use manual package updates.

After branding and updater acceptance, resume the owner test of Full Search with matching network, catalog settings, timeout and concurrency. Compare elapsed time and status counts with the earlier 121 timeouts in 9 min 45 s. Review Verified and Possible Match accuracy, legitimate platform coverage, actual icons, radar markers, optional sound, cancellation, native profile opening, exports, local settings and optional history. Use **Export diagnostics (no handle or URLs)** for a local diagnostic report. [Measurement checklist](catalog-audit.md#measuring-an-owner-side-run)

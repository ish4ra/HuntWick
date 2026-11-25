# Packaging and installation

Build the sidecar on each target OS and architecture first, as described in [development](development.md). Install workspace dependencies with the lockfiles. Run `cargo fetch --manifest-path src-tauri/Cargo.toml --locked` and `python scripts/desktop_notices.py` before bundling. Use the native target from this table.

| Build machine | Rust target | Tauri bundles |
| --- | --- | --- |
| Windows x64 | x86_64-pc-windows-msvc | nsis |
| macOS Apple Silicon | aarch64-apple-darwin | dmg |
| macOS Intel | x86_64-apple-darwin | dmg |
| Linux x64 | x86_64-unknown-linux-gnu | deb,appimage |

```sh
npm run tauri -- build --ci --target <target> --bundles <bundles> -- --locked
```

The CI workflow attempts all four targets and uploads test installers and checksums from successful jobs. Use the run for the exact commit you want and download the matching artifact. Verify installer hashes against that run's manifest after extracting the archive. GitHub may require sign-in to download Actions artifacts.

On Windows, compare `Get-FileHash -Algorithm SHA256 <installer.exe>` with the manifest. Run the verified installer. SmartScreen may flag an unsigned build. Verify provenance with the project before proceeding and keep system-wide protection enabled.

On macOS, run `shasum -a 256 <image.dmg>`, open the verified image and drag HuntWick into Applications. Builds without a Developer ID and notarization may trigger Gatekeeper. If you trust the source and verified the checksum, use Apple's app-specific **Open Anyway** option in **System Settings → Privacy & Security** after trying to open it. Managed Macs may require administrator approval. [Apple's guidance](https://support.apple.com/en-us/102445)

On Linux, run `sha256sum <installer>`. Install the Debian package through your distribution's package installer to resolve OS libraries, or mark the AppImage executable and launch it on a compatible x64 system with FUSE support. The engine is included in both formats.

The release workflow requires manual dispatch. Review all platform checks and artifact hashes before publishing a tagged release. CI test builds can be evaluated independently of release publication.
## Update signing and recovery

Use the standalone Apple Silicon signer and GitHub repository settings to prepare the permanent key. The handover includes the artifact-only build path and the RC.3 to RC.4 device test. [Owner signing and update guide](production-updater.md)

The manual release workflow requires signing material. It uploads the platform artifacts and version-specific manifest to a versioned release and updates the selected GitHub Releases feed. Preview is opt-in. Normal matrix builds sign disposable test artifacts. A build without a configured verification key directs the user to manual downloads. Linux DEB uses manual package installation. Compare the installer SHA256 with the versioned release manifest. macOS Gatekeeper and Developer ID notarization are separate from Tauri signatures. Follow the unsigned-build instructions above.

Production acceptance requires installing one version and updating to a newer signed build on representative devices, checking retained preferences, cancellation, tamper rejection and restart. Owner approval is required before enabling the public feed.

# Local development

Use Node 24 and npm, the Rust toolchain specified by the CI workflow, Python 3.12 for building the sidecar, and uv. End users install the desktop package. Only contributors need these tools.

Install the Tauri 2 prerequisites for your build host. Windows requires the MSVC C++ build tools and WebView2. macOS requires Xcode command-line tools. On Debian or Ubuntu install a compiler, pkg-config, WebKitGTK 4.1 development headers, GTK 3, librsvg, OpenSSL development headers and the bundling utilities used by CI. [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/)

Run these commands from the repository root.

```sh
npm ci
uv sync --project engine --frozen --python 3.12
uv run --project engine --frozen python engine/build.py
npm run tauri -- dev
```

The desktop host must be able to find the entire packaged engine directory. A frontend-only session started with `npm run dev` supports interface work. Native searches and local file dialogs require the Tauri host.

## Verification

```sh
npm run lint
npm run typecheck
npm test
npm run build
uv run --project engine --frozen python -m unittest discover -s engine/tests
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
cargo clippy --manifest-path src-tauri/Cargo.toml --locked --all-targets -- -D warnings
cargo test --manifest-path src-tauri/Cargo.toml --locked
```

Use synthetic fixtures in automated tests. For a limited manual live check, use an account you control or a synthetic handle, disable unrelated platforms, run Search, then open or export a result. Test cancellation on a separate run. Rate limits and inconclusive responses are valid outcomes.

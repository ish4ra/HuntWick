# Architecture

A single local Tauri window owns the React workspace. The Rust host loads packaged HTML, JavaScript and CSS into the operating system's webview. Static assets include the application and platform UI icons. A search does not require a HuntWick server, account or token.

## Engine boundary

The frontend sends a request ID, username, selected site names, concurrency and timeout to the native host. The host starts the installed engine executable at a fixed resource path. The request crosses standard input as JSON. The engine emits newline-delimited JSON records as sites complete. A catalog request uses the same executable and data as a search. Counts derive from compatible entries. The UI never needs to invoke a terminal or parse Sherlock's display output.

Sherlock's Python package has a library entry point, result types and notifier hooks, although its internal API can change. HuntWick pins the release, supplies an immutable site snapshot, and adapts upstream results into stable desktop statuses. Additional checks conservatively handle generic responses, missing evidence and rate limits. This can miss real profiles. A found profile is evidence about a public handle only.

The search event carries a request ID at the Rust-to-window boundary. The model ignores superseded events and duplicate platform results. Explicit terminal states let the UI represent cancellation, failure and partial results. Another engine could implement the same catalog and search protocol without exposing its command line to React.

## Packaging decision

Use a PyInstaller directory bundle built on each native target. It carries its interpreter, library modules, TLS roots and data alongside the executable. This avoids bootstrapping Python at install time and extracting an entire single-file archive at every search. The installer and the engine must have matching architectures. The desktop app uses OS browser components, so Linux distributions still need compatible GTK and WebKit libraries.

## Local state

Settings and opt-in history use the application webview's origin-scoped local storage. This keeps a small local history without a database service or a second native API. Treat saved history and exported files as ordinary local data accessible to processes with access to the user's profile. There is no synchronization or application-level encryption.

## Trust boundaries

Only the application window receives the defined native commands. Rust validates request shapes and site selections, and manages process termination. The adapter loads pinned data and bounds parallel requests. The frontend treats every result as text. Exporting crosses a native save dialog and opening a profile delegates a validated HTTPS address to the system browser. Site HTML stays out of the webview.

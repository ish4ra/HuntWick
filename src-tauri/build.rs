fn main() {
    const COMMANDS: &[&str] = &[
        "catalog",
        "confirm_install",
        "start_search",
        "cancel_search",
        "save_export",
        "open_url",
    ];
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(COMMANDS)),
    )
    .expect("failed to prepare HuntWick desktop resources");
}

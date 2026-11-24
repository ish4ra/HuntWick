use super::Engine;
use serde::Serialize;
use std::{sync::Mutex, time::Duration};
use tauri::{AppHandle, Emitter, State};
use tauri_plugin_updater::{Update, UpdaterExt};

#[derive(Default)]
pub struct Pending(Mutex<Option<Update>>);

#[derive(Serialize)]
pub struct Offer {
    version: String,
    notes: String,
}

const RELEASES: &str = "https://github.com/ish4ra/HuntWick/releases/download/";
fn approved_url(url: &str) -> bool {
    url.starts_with(RELEASES)
        && !url.contains('?')
        && !url.contains('#')
        && !url.contains('%')
        && !url.split('/').any(|s| matches!(s, "." | ".."))
}

#[tauri::command]
pub async fn check_update(
    app: AppHandle,
    pending: State<'_, Pending>,
    prerelease: bool,
) -> Result<Option<Offer>, String> {
    let key = option_env!("HUNTWICK_UPDATER_PUBLIC_KEY")
        .filter(|k| !k.trim().is_empty())
        .ok_or(
            "This build has no release verification key. Use the checksummed manual downloads.",
        )?;
    if cfg!(target_os = "linux") && std::env::var_os("APPIMAGE").is_none() {
        return Err(
            "Use the signed release and its checksum to update your Debian package.".into(),
        );
    }
    let channel = if prerelease { "preview" } else { "stable" };
    let endpoint = format!("{RELEASES}updates-{channel}/latest.json")
        .parse()
        .map_err(|_| "Invalid feed.")?;
    let updater = app
        .updater_builder()
        .pubkey(key)
        .timeout(Duration::from_secs(20))
        .endpoints(vec![endpoint])
        .map_err(|_| "Invalid release feed.")?
        .version_comparator(move |current, remote| {
            remote.version > current && (prerelease || remote.version.pre.is_empty())
        })
        .build()
        .map_err(|_| "Updater is unavailable on this installation.")?;
    let update = updater
        .check()
        .await
        .map_err(|_| "The signed update feed could not be checked. Retry or open Releases.")?;
    if update
        .as_ref()
        .is_some_and(|u| !approved_url(u.download_url.as_str()) || u.signature.is_empty())
    {
        return Err("The release metadata is invalid.".into());
    }
    let offer = update.as_ref().map(|u| Offer {
        version: u.version.clone(),
        notes: u.body.clone().unwrap_or_default(),
    });
    *pending.0.lock().unwrap() = update;
    Ok(offer)
}

#[tauri::command]
pub async fn install_update(
    app: AppHandle,
    engine: State<'_, Engine>,
    pending: State<'_, Pending>,
    version: String,
) -> Result<(), String> {
    let update = {
        let mut runtime = engine.runtime.lock().unwrap();
        if runtime.search.is_some()
            || runtime.loading.is_some()
            || runtime.updating
            || runtime.shutting_down
        {
            return Err("Finish or cancel the active operation before installing.".into());
        }
        let mut offer = pending.0.lock().unwrap();
        if offer.as_ref().map(|u| &u.version) != Some(&version) {
            return Err("Check for updates again.".into());
        }
        runtime.updating = true;
        offer.take().unwrap()
    };
    let mut bytes = 0u64;
    let result = update
        .download_and_install(
            |chunk, total| {
                bytes += chunk as u64;
                let _ = app.emit_to("main", "update-progress", (bytes, total));
            },
            || {},
        )
        .await;
    if result.is_ok() {
        app.restart();
    }
    engine.runtime.lock().unwrap().updating = false;
    Err("Update verification or installation failed. Check again to retry.".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn downloads_are_pinned_to_release_assets() {
        assert!(approved_url(
            "https://github.com/ish4ra/HuntWick/releases/download/v1/file"
        ));
        for other in [
            "http://github.com/ish4ra/HuntWick/releases/download/v1/file",
            "https://github.com/other/HuntWick/releases/download/v1/file",
            "https://github.com/ish4ra/HuntWick/releases/download/../../other",
            "https://github.com/ish4ra/HuntWick/releases/download/%2fother",
        ] {
            assert!(!approved_url(other));
        }
    }
}

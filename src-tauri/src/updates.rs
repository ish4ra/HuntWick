use super::Engine;
use serde::Serialize;
use std::{sync::Mutex, time::Duration};
use tauri::{AppHandle, Emitter, State};
use tauri_plugin_updater::{Error as UpdateError, Update, UpdaterExt};

#[derive(Default)]
pub struct Pending(Mutex<Option<Update>>);

#[derive(Serialize)]
pub struct Offer {
    version: String,
    notes: String,
}

pub(super) const EMBEDDED_KEY: Option<&str> = option_env!("HUNTWICK_UPDATER_PUBLIC_KEY");

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
    *pending.0.lock().unwrap() = None;
    let key = EMBEDDED_KEY.filter(|k| !k.trim().is_empty()).ok_or(
        "This build has no release verification key. Use the checksummed manual downloads.",
    )?;
    if cfg!(target_os = "linux") && std::env::var_os("APPIMAGE").is_none() {
        return Err(
            "Use the signed release and its checksum to update your Debian package.".into(),
        );
    }
    let channel = if prerelease { "preview" } else { "stable" };
    let endpoint: url::Url = format!("{RELEASES}updates-{channel}/latest.json")
        .parse()
        .map_err(|_| "Invalid feed.")?;
    let updater = app
        .updater_builder()
        .pubkey(key)
        .timeout(Duration::from_secs(20))
        .endpoints(vec![endpoint.clone()])
        .map_err(|_| "Invalid release feed.")?
        .version_comparator(move |current, remote| {
            remote.version > current && (prerelease || remote.version.pre.is_empty())
        })
        .build()
        .map_err(|_| "Updater is unavailable on this installation.")?;
    let update = match updater.check().await {
        Ok(offer) => offer,
        Err(UpdateError::ReleaseNotFound) => {
            // The plugin discards non-success HTTP statuses. Only a confirmed 404
            // from this fixed release endpoint establishes an unpublished feed.
            let client = reqwest::Client::builder()
                .timeout(Duration::from_secs(8))
                .build()
                .map_err(|_| "The update service is unavailable.")?;
            let missing = client
                .head(endpoint)
                .send()
                .await
                .is_ok_and(|r| r.status().as_u16() == 404);
            return Err(if missing {
                "No feed has been published on this channel."
            } else {
                "The update service is unavailable. Try again later."
            }
            .into());
        }
        Err(UpdateError::Reqwest(e)) if !e.is_decode() => {
            return Err("Could not reach the update service. Check your connection.".into())
        }
        Err(_) => {
            return Err("The release metadata is invalid or does not support this platform.".into())
        }
    };
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
    match result {
        Err(
            UpdateError::Minisign(_)
            | UpdateError::Base64(_)
            | UpdateError::SignatureUtf8(_)
            | UpdateError::SignedVersionMismatch { .. }
            | UpdateError::MissingSignedVersion,
        ) => Err("Update signature verification failed. The update was rejected.".into()),
        Err(UpdateError::Reqwest(_) | UpdateError::Network(_)) => {
            Err("The update download failed. Check your connection and retry.".into())
        }
        _ => Err("Installation failed. Check again or use the manual installer.".into()),
    }
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

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
    let stable = check_channel(&app, key, "stable").await;
    let update = if prerelease {
        let preview = check_channel(&app, key, "preview").await;
        match (stable, preview) {
            (Err(a), Err(b)) => return Err(if a == MISSING_FEED { b } else { a }),
            (Err(e), Ok(other)) | (Ok(other), Err(e)) if e == MISSING_FEED => other,
            (Err(e), _) | (_, Err(e)) => return Err(e),
            (Ok(Some(stable)), Ok(Some(preview))) => {
                if preview_is_newer(&stable.version, &preview.version)? {
                    Some(preview)
                } else {
                    Some(stable)
                }
            }
            (Ok(stable), Ok(preview)) => stable.or(preview),
        }
    } else {
        stable?
    };
    let offer = update.as_ref().map(|u| Offer {
        version: u.version.clone(),
        notes: u.body.clone().unwrap_or_default(),
    });
    *pending.0.lock().unwrap() = update;
    Ok(offer)
}

const MISSING_FEED: &str =
    "No update feed has been published for this channel yet. Check again after the next release.";

fn preview_is_newer(stable: &str, preview: &str) -> Result<bool, String> {
    let parse =
        |v: &str| semver::Version::parse(v).map_err(|_| "Invalid release version.".to_owned());
    Ok(parse(preview)?.cmp_precedence(&parse(stable)?).is_gt())
}

async fn check_channel(
    app: &AppHandle,
    key: &str,
    channel: &str,
) -> Result<Option<Update>, String> {
    let prerelease = channel == "preview";
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
            remote.version.cmp_precedence(&current).is_gt()
                && (prerelease || remote.version.pre.is_empty())
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
                MISSING_FEED
            } else {
                "The update service is unavailable. Try again later."
            }
            .into());
        }
        Err(UpdateError::Reqwest(e)) if !e.is_decode() => {
            return Err("Could not reach the update service. Check your connection and try Check for updates again.".into())
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
    Ok(update)
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
        ) => Err("Update signature verification failed. HuntWick rejected the download. Check again for a signed release.".into()),
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
    fn preview_must_outrank_stable() {
        assert!(!preview_is_newer("1.10.0", "1.9.0-rc.10").unwrap());
        assert!(!preview_is_newer("1.0.0", "1.0.0-rc.99").unwrap());
        assert!(!preview_is_newer("1.0.0+1", "1.0.0+2").unwrap());
        assert!(preview_is_newer("1.0.0", "1.1.0-rc.1").unwrap());
    }
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

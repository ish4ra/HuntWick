#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod dialog;
mod process;
mod protocol;

use process::{communicate, Process};
use protocol::{public_https, read_catalog, stream_search, Catalog, Profile, SearchRequest};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::{
    io::Write,
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
    time::Duration,
};
use tauri::{AppHandle, Emitter, Manager, State};

#[derive(Default)]
struct Runtime {
    shutting_down: bool,
    catalog: Option<Catalog>,
    loading: Option<Arc<Process>>,
    search: Option<ActiveSearch>,
}

struct ActiveSearch {
    id: String,
    process: Arc<Process>,
}

#[derive(Default)]
struct Engine {
    runtime: Mutex<Runtime>,
    catalog_gate: tokio::sync::Mutex<()>,
}

#[derive(Clone, Serialize)]
#[serde(tag = "type", rename_all = "lowercase")]
enum Event<'a> {
    Result {
        id: &'a str,
        #[serde(flatten)]
        profile: Profile,
    },
    Done {
        id: &'a str,
    },
    Error {
        id: &'a str,
        message: String,
    },
}

fn engine_path(app: &AppHandle) -> Result<PathBuf, String> {
    let dir = app
        .path()
        .resource_dir()
        .map_err(|_| "Cannot locate application resources.")?;
    Ok(dir
        .join("engine")
        .join(format!("huntwick-engine{}", std::env::consts::EXE_SUFFIX)))
}

async fn run_worker<T: Send + 'static>(
    process: Arc<Process>,
    deadline: Duration,
    work: impl FnOnce() -> Result<T, String> + Send + 'static,
) -> Result<T, String> {
    let worker = tauri::async_runtime::spawn_blocking(work);
    let result = match tokio::time::timeout(deadline, worker).await {
        Ok(Ok(value)) => value,
        Ok(Err(_)) => Err("The local engine worker stopped unexpectedly.".into()),
        Err(_) => Err("The local engine exceeded its time limit.".into()),
    };
    process.stop();
    result
}

#[tauri::command]
async fn catalog(app: AppHandle, state: State<'_, Engine>) -> Result<Catalog, String> {
    let _gate = state.catalog_gate.lock().await;
    let (process, input, output) = {
        let mut runtime = state.runtime.lock().unwrap();
        if runtime.shutting_down {
            return Err("The application is closing.".into());
        }
        if let Some(catalog) = &runtime.catalog {
            return Ok(catalog.clone());
        }
        let handles = Process::spawn(&engine_path(&app)?)?;
        runtime.loading = Some(handles.0.clone());
        handles
    };
    let value = run_worker(process.clone(), Duration::from_secs(60), move || {
        communicate(
            &process,
            input,
            output,
            &json!({"op":"catalog"}),
            read_catalog,
        )
    })
    .await;
    let mut runtime = state.runtime.lock().unwrap();
    runtime.loading.take();
    let catalog = value?;
    runtime.catalog = Some(catalog.clone());
    Ok(catalog)
}

#[tauri::command]
async fn start_search(
    app: AppHandle,
    state: State<'_, Engine>,
    request: SearchRequest,
) -> Result<(), String> {
    let (process, input, output) = {
        let mut runtime = state.runtime.lock().unwrap();
        if runtime.shutting_down {
            return Err("The application is closing.".into());
        }
        if runtime.search.is_some() {
            return Err("A search is already running.".into());
        }
        let catalog = runtime
            .catalog
            .as_ref()
            .ok_or("Load the platform catalog before searching.")?;
        request.validate(catalog)?;
        let handles = Process::spawn(&engine_path(&app)?)?;
        runtime.search = Some(ActiveSearch {
            id: request.id.clone(),
            process: handles.0.clone(),
        });
        handles
    };

    tauri::async_runtime::spawn(async move {
        let batches = request.sites.len().div_ceil(request.concurrency as usize) as u64;
        let deadline = Duration::from_secs(60 + batches * (request.timeout as u64 * 3 + 5));
        let reader_app = app.clone();
        let reader_process = process.clone();
        let result = run_worker(process.clone(), deadline, move || {
            let operation = json!({ "op":"search", "username":request.username, "sites":request.sites,
                                    "timeout":request.timeout, "concurrency":request.concurrency });
            communicate(&reader_process, input, output, &operation, |reader| {
                stream_search(reader, &request.sites, |profile| {
                    let state = reader_app.state::<Engine>();
                    let runtime = state.runtime.lock().unwrap();
                    let active = runtime.search.as_ref()
                        .filter(|active| Arc::ptr_eq(&active.process, &reader_process))
                        .ok_or("The search was cancelled.")?;
                    reader_app.emit_to("main", "engine-event", Event::Result { id: &active.id, profile })
                        .map_err(|_| "Could not deliver a search result.".to_owned())
                })
            })
        }).await;

        let state = app.state::<Engine>();
        let mut runtime = state.runtime.lock().unwrap();
        if runtime
            .search
            .as_ref()
            .is_some_and(|s| Arc::ptr_eq(&s.process, &process))
        {
            let active = runtime.search.take().unwrap();
            let event = match result {
                Ok(()) => Event::Done { id: &active.id },
                Err(message) => Event::Error {
                    id: &active.id,
                    message,
                },
            };
            let _ = app.emit_to("main", "engine-event", event);
        }
    });
    Ok(())
}

#[tauri::command]
async fn cancel_search(state: State<'_, Engine>, id: String) -> Result<(), String> {
    let mut runtime = state.runtime.lock().unwrap();
    if runtime.search.as_ref().is_some_and(|s| s.id == id) {
        runtime.search.take().unwrap().process.stop();
    }
    Ok(())
}

#[tauri::command]
async fn open_url(url: String) -> Result<(), String> {
    public_https(&url)?;
    open::that_detached(url).map_err(|_| "Could not open the system browser.".into())
}

#[derive(Deserialize)]
#[serde(rename_all = "lowercase")]
enum ExportFormat {
    Json,
    Csv,
    Html,
}

fn write_export(path: &Path, contents: &[u8]) -> Result<(), String> {
    let failure = || "Could not save the export to the selected file.".to_string();
    let parent = path.parent().ok_or_else(failure)?;
    let mut file = tempfile::NamedTempFile::new_in(parent).map_err(|_| failure())?;
    file.write_all(contents).map_err(|_| failure())?;
    file.as_file().sync_all().map_err(|_| failure())?;
    file.persist(path).map_err(|_| failure())?;
    Ok(())
}

#[tauri::command]
async fn save_export(
    window: tauri::WebviewWindow,
    format: ExportFormat,
    contents: String,
) -> Result<bool, String> {
    if contents.len() > 8 * 1024 * 1024 {
        return Err("The export exceeds the 8 MiB limit.".into());
    }
    let extension = match format {
        ExportFormat::Json => "json",
        ExportFormat::Csv => "csv",
        ExportFormat::Html => "html",
    };
    let Some(path) = dialog::choose_export(window, extension).await? else {
        return Ok(false);
    };
    if !path
        .extension()
        .and_then(|s| s.to_str())
        .is_some_and(|s| s.eq_ignore_ascii_case(extension))
    {
        return Err(format!("Choose a filename ending in .{extension}."));
    }
    tauri::async_runtime::spawn_blocking(move || write_export(&path, contents.as_bytes()))
        .await
        .map_err(|_| "The file could not be saved.".to_string())??;
    Ok(true)
}

fn main() {
    tauri::Builder::default()
        .manage(Engine::default())
        .invoke_handler(tauri::generate_handler![
            catalog,
            start_search,
            cancel_search,
            open_url,
            save_export
        ])
        .build(tauri::generate_context!())
        .expect("could not initialize HuntWick")
        .run(|app, event| {
            if matches!(event, tauri::RunEvent::Exit) {
                let engine = app.state::<Engine>();
                let mut runtime = engine.runtime.lock().unwrap();
                runtime.shutting_down = true;
                if let Some(active) = runtime.search.take() {
                    active.process.stop();
                }
                if let Some(process) = runtime.loading.take() {
                    process.stop();
                }
            }
        });
}

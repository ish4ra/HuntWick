use std::path::PathBuf;
use tauri::WebviewWindow;

#[cfg(target_os = "linux")]
pub async fn choose_export(
    window: WebviewWindow,
    extension: &'static str,
) -> Result<Option<PathBuf>, String> {
    use gtk::prelude::*;
    let (sender, selection) = tokio::sync::oneshot::channel();
    let parent_window = window.clone();
    window
        .run_on_main_thread(move || {
            let Ok(parent) = parent_window.gtk_window() else {
                return;
            };
            let chooser = gtk::FileChooserNative::new(
                Some("Save search results"),
                Some(&parent),
                gtk::FileChooserAction::Save,
                Some("Save"),
                Some("Cancel"),
            );
            chooser.set_modal(true);
            chooser.set_do_overwrite_confirmation(true);
            chooser.set_current_name(&format!("huntwick-results.{extension}"));
            let filter = gtk::FileFilter::new();
            filter.set_name(Some(&extension.to_uppercase()));
            filter.add_pattern(&format!("*.{extension}"));
            chooser.add_filter(filter);
            gtk::glib::MainContext::default().spawn_local(async move {
                let response = chooser.run_future().await;
                let path = if response == gtk::ResponseType::Accept {
                    chooser.filename()
                } else {
                    None
                };
                chooser.destroy();
                let _ = sender.send(path);
            });
        })
        .map_err(|_| "Could not open the save dialog.")?;
    selection
        .await
        .map_err(|_| "The save dialog closed unexpectedly.".into())
}

#[cfg(not(target_os = "linux"))]
pub async fn choose_export(
    window: WebviewWindow,
    extension: &'static str,
) -> Result<Option<PathBuf>, String> {
    let selection = rfd::AsyncFileDialog::new()
        .set_parent(&window)
        .set_title("Save search results")
        .set_file_name(format!("huntwick-results.{extension}"))
        .add_filter(extension.to_uppercase(), &[extension])
        .save_file()
        .await;
    Ok(selection.map(|file| file.path().to_owned()))
}

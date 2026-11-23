use command_group::{CommandGroup, GroupChild};
use serde::Serialize;
use std::{
    io::{BufReader, Write},
    path::Path,
    process::{ChildStdin, ChildStdout, Command, Stdio},
    sync::{Arc, Mutex},
    time::Duration,
};

pub struct Process(Mutex<Option<GroupChild>>);

impl Process {
    pub fn spawn(path: &Path) -> Result<(Arc<Self>, ChildStdin, ChildStdout), String> {
        let mut command = Command::new(path);
        command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        let mut group = command.group();
        #[cfg(windows)]
        group.kill_on_drop(true).creation_flags(0x08000000); // CREATE_NO_WINDOW
        let mut child = group
            .spawn()
            .map_err(|_| "Could not start the bundled local engine.")?;
        let input = child
            .inner()
            .stdin
            .take()
            .expect("stdin configured as piped");
        let output = child
            .inner()
            .stdout
            .take()
            .expect("stdout configured as piped");
        Ok((Arc::new(Self(Mutex::new(Some(child)))), input, output))
    }

    pub fn stop(&self) {
        if let Some(mut child) = self.0.lock().unwrap().take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }

    fn wait_success(&self) -> Result<(), String> {
        loop {
            {
                let mut slot = self.0.lock().unwrap();
                let child = slot.as_mut().ok_or("The search was cancelled.")?;
                if let Some(status) = child
                    .try_wait()
                    .map_err(|_| "Could not wait for the local engine.")?
                {
                    slot.take();
                    return if status.success() {
                        Ok(())
                    } else {
                        Err("The local engine stopped unexpectedly.".into())
                    };
                }
            }
            std::thread::sleep(Duration::from_millis(10));
        }
    }
}

impl Drop for Process {
    fn drop(&mut self) {
        self.stop();
    }
}

pub fn communicate<T>(
    process: &Process,
    mut input: ChildStdin,
    output: ChildStdout,
    request: &impl Serialize,
    parse: impl FnOnce(BufReader<ChildStdout>) -> Result<T, String>,
) -> Result<T, String> {
    serde_json::to_writer(&mut input, request).map_err(|_| "Could not send the engine request.")?;
    input
        .write_all(b"\n")
        .map_err(|_| "Could not send the engine request.")?;
    drop(input);
    let value = parse(BufReader::new(output))?;
    process.wait_success()?;
    Ok(value)
}

#[cfg(test)]
#[path = "process_tests.rs"]
mod tests;

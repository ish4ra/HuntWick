use super::*;
use std::io::BufRead;
use std::path::PathBuf;

// cargo places the test binary in <profile>/deps and bundled resources in <profile>.
fn bundled_engine() -> PathBuf {
    let binary = std::env::current_exe().unwrap();
    binary
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .join("engine")
        .join(format!("huntwick-engine{}", std::env::consts::EXE_SUFFIX))
}

#[test]
fn cancellation_closes_the_process_and_wakes_the_reader() {
    let (process, _input, output) = Process::spawn(&bundled_engine()).unwrap();
    // The engine is waiting for one request on stdin. Killing it must unblock stdout
    // even while the parent still owns the write end of the input pipe.
    process.stop();
    assert!(BufReader::new(output).fill_buf().unwrap().is_empty());
    assert!(process.wait_success().is_err());
    process.stop();
}

#[test]
fn bundled_engine_reads_a_request_returns_catalog_and_exits_cleanly() {
    let (process, input, output) = Process::spawn(&bundled_engine()).unwrap();
    let request = serde_json::json!({"op":"catalog"});
    let catalog = communicate(
        &process,
        input,
        output,
        &request,
        crate::protocol::read_catalog,
    )
    .unwrap();
    assert!(catalog
        .sites
        .iter()
        .any(|entry| entry.name == "GitHub" && entry.quick));
    process.stop();
}

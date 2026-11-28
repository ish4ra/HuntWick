use super::*;
use serde_json::json;
use std::io::Cursor;

fn catalog() -> Catalog {
    serde_json::from_value(json!({
        "version":"0.16.2", "databaseVersion":"abc", "updatedAt":"2026-11-22",
        "sites":[{"name":"GitHub","url":"https://github.com","category":"Coding","quick":true}]
    }))
    .unwrap()
}

fn request() -> SearchRequest {
    serde_json::from_value(json!({
        "id":"scan-1", "username":"a_1-b.c", "sites":["GitHub"], "timeout":1, "concurrency":20
    }))
    .unwrap()
}

#[test]
fn bounds_and_catalog_membership_are_enforced_before_spawn() {
    assert!(request().validate(&catalog()).is_ok());
    for handle in ["", "..", ".", "a/b", "line\n", "@foo", &"a".repeat(65)] {
        assert!(SearchRequest {
            username: handle.into(),
            ..request()
        }
        .validate(&catalog())
        .is_err());
    }
    for sites in [vec![], vec!["bad".into()], vec!["GitHub".into(); 2]] {
        assert!(SearchRequest { sites, ..request() }
            .validate(&catalog())
            .is_err());
    }
    for (timeout, concurrency) in [(0, 1), (61, 1), (1, 0), (1, 21)] {
        assert!(SearchRequest {
            timeout,
            concurrency,
            ..request()
        }
        .validate(&catalog())
        .is_err());
    }
}

#[test]
fn external_urls_use_public_https_without_credentials() {
    assert!(public_https("https://example.com/@alice?tab=posts").is_ok());
    for url in [
        "file:///tmp/test",
        "https://example.com@localhost/x",
        "http://example.com",
        "https://user@example.com",
        "https://127.0.0.1/p",
        "https://[::1]/p",
        "https://localhost./",
        "https://sub.localhost/",
        "https://test.local/",
        "https://example.com:8443/p",
        "https://example.com\n/x",
    ] {
        assert!(public_https(url).is_err(), "accepted {url}");
    }
}

#[test]
fn oversized_and_unterminated_frames_are_rejected() {
    assert_eq!(
        read_frame(&mut Cursor::new(b"{}\n"), 3).unwrap().unwrap(),
        b"{}"
    );
    assert!(read_frame(&mut Cursor::new(b"{}{}\n"), 3).is_err());
    assert!(read_frame(&mut Cursor::new(b"{}"), 3).is_err());
    assert!(read_frame(&mut Cursor::new(b""), 3).unwrap().is_none());
}

#[test]
fn missing_duplicate_and_unsolicited_results_are_protocol_errors() {
    let result =
        r#"{"type":"result","platform":"GitHub","url":"https://github.com/abc","status":"found"}"#;
    let done = r#"{"type":"done"}"#;
    let run = |lines: &[&str]| {
        let bytes = format!("{}\n", lines.join("\n"));
        stream_search(Cursor::new(bytes), &request().sites, |_| Ok(()))
    };
    assert!(run(&[result, done]).is_ok());
    assert!(run(&[done]).is_err());
    assert!(run(&[result, result, done]).is_err());
    assert!(run(&[result]).is_err());
    assert!(run(&[&result.replace("GitHub", "Other"), done]).is_err());
    assert!(run(&[result, done, result]).is_err());
}

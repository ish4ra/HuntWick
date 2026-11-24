use serde::{Deserialize, Serialize};
use std::{
    collections::HashSet,
    io::{BufRead, Read},
};
use url::{Host, Url};

#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Catalog {
    pub version: String,
    pub database_version: String,
    pub updated_at: String,
    pub sites: Vec<Site>,
    #[serde(default)]
    pub unavailable: Vec<Unavailable>,
}

#[derive(Clone, Deserialize, Serialize)]
pub struct Unavailable {
    pub name: String,
    pub reason: String,
}

#[derive(Clone, Deserialize, Serialize)]
pub struct Site {
    pub name: String,
    pub url: String,
    pub category: String,
    pub quick: bool,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SearchRequest {
    pub id: String,
    pub username: String,
    pub sites: Vec<String>,
    pub timeout: u8,
    pub concurrency: u8,
}

const BAD_FRAME: &str = "The local engine returned an invalid response.";
const CATALOG_LIMIT: u64 = 1024 * 1024;
const RESULT_LIMIT: u64 = 16 * 1024;

impl Catalog {
    fn validate(&self) -> Result<(), String> {
        let mut names = HashSet::new();
        if self.sites.is_empty()
            || self.sites.len() > 1024
            || self.sites.iter().any(|s| {
                s.name.is_empty()
                    || s.name.len() > 160
                    || !names.insert(&s.name)
                    || public_https(&s.url).is_err()
            })
        {
            return Err("The bundled platform catalog is invalid.".into());
        }
        Ok(())
    }
}

impl SearchRequest {
    pub fn validate(&self, catalog: &Catalog) -> Result<(), String> {
        if self.id.is_empty()
            || self.id.len() > 96
            || !self
                .id
                .bytes()
                .all(|c| c.is_ascii_alphanumeric() || matches!(c, b'-' | b'_'))
        {
            return Err("Invalid search ID.".into());
        }
        if self.username.is_empty()
            || self.username.len() > 64
            || matches!(self.username.as_str(), "." | "..")
            || !self
                .username
                .bytes()
                .all(|c| c.is_ascii_alphanumeric() || matches!(c, b'_' | b'-' | b'.'))
        {
            return Err(
                "Enter a username of 1–64 letters, digits, dots, dashes or underscores.".into(),
            );
        }
        if !(1..=60).contains(&self.timeout) || !(1..=20).contains(&self.concurrency) {
            return Err("Timeout must be 1–60 seconds and concurrency must be 1–20.".into());
        }
        let available: HashSet<&str> = catalog.sites.iter().map(|s| s.name.as_str()).collect();
        let mut selected = HashSet::new();
        if self.sites.is_empty()
            || self.sites.len() > available.len()
            || self
                .sites
                .iter()
                .any(|site| !available.contains(site.as_str()) || !selected.insert(site))
        {
            return Err("Select unique platforms from the bundled catalog.".into());
        }
        Ok(())
    }
}

pub fn public_https(raw: &str) -> Result<(), String> {
    let invalid = || "Only public HTTPS links can be opened.".to_owned();
    if !raw.starts_with("https://")
        || raw.len() > 4096
        || raw
            .chars()
            .any(|c| c.is_control() || c.is_whitespace() || c == '\\')
    {
        return Err(invalid());
    }
    let parsed = Url::parse(raw).map_err(|_| invalid())?;
    let Some(Host::Domain(domain)) = parsed.host() else {
        return Err(invalid());
    };
    let domain = domain.trim_end_matches('.');
    if !domain.contains('.')
        || domain.ends_with(".localhost")
        || domain.ends_with(".local")
        || domain.ends_with(".internal")
        || !parsed.username().is_empty()
        || parsed.password().is_some()
        || parsed.port().is_some()
    {
        return Err(invalid());
    }
    Ok(())
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Found,
    Possible,
    NotFound,
    Inconclusive,
    TimedOut,
    Blocked,
    Cancelled,
    Error,
}

#[derive(Clone, Deserialize, Serialize)]
pub struct Profile {
    pub platform: String,
    pub url: String,
    pub status: Status,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
}

#[derive(Deserialize)]
#[serde(tag = "type", rename_all = "lowercase")]
enum Frame {
    Catalog(Catalog),
    Result(Profile),
    Done,
    Error,
}

pub fn read_frame(reader: &mut impl BufRead, limit: u64) -> Result<Option<Vec<u8>>, String> {
    let mut bytes = Vec::new();
    reader
        .take(limit + 1)
        .read_until(b'\n', &mut bytes)
        .map_err(|_| BAD_FRAME)?;
    if bytes.is_empty() {
        return Ok(None);
    }
    if bytes.len() as u64 > limit || bytes.pop() != Some(b'\n') {
        return Err(BAD_FRAME.into());
    }
    Ok(Some(bytes))
}

fn next(reader: &mut impl BufRead, limit: u64) -> Result<Option<Frame>, String> {
    read_frame(reader, limit)?
        .map(|bytes| serde_json::from_slice::<Frame>(&bytes).map_err(|_| BAD_FRAME.to_owned()))
        .transpose()
}

fn expect_eof(reader: &mut impl BufRead) -> Result<(), String> {
    if reader.fill_buf().map_err(|_| BAD_FRAME)?.is_empty() {
        Ok(())
    } else {
        Err(BAD_FRAME.into())
    }
}

pub fn read_catalog(mut reader: impl BufRead) -> Result<Catalog, String> {
    let Some(Frame::Catalog(catalog)) = next(&mut reader, CATALOG_LIMIT)? else {
        return Err("Could not load the local engine catalog.".into());
    };
    catalog.validate()?;
    if !matches!(next(&mut reader, RESULT_LIMIT)?, Some(Frame::Done)) {
        return Err(BAD_FRAME.into());
    }
    expect_eof(&mut reader)?;
    Ok(catalog)
}

pub fn stream_search(
    mut reader: impl BufRead,
    sites: &[String],
    mut emit: impl FnMut(Profile) -> Result<(), String>,
) -> Result<(), String> {
    let mut pending: HashSet<&str> = sites.iter().map(String::as_str).collect();
    loop {
        match next(&mut reader, RESULT_LIMIT)? {
            Some(Frame::Result(profile)) if pending.remove(profile.platform.as_str()) => {
                public_https(&profile.url)?;
                emit(profile)?;
            }
            Some(Frame::Done) if pending.is_empty() => return expect_eof(&mut reader),
            Some(Frame::Error) => return Err("The local search engine reported a failure.".into()),
            _ => return Err(BAD_FRAME.into()),
        }
    }
}

#[cfg(test)]
#[path = "protocol_tests.rs"]
mod tests;

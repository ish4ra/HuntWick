use semver::Version;

#[derive(Debug, PartialEq)]
pub(super) enum Choice {
    Stable,
    Preview,
    PreviewNotice,
    Current,
}

pub(super) fn eligible_version(current: &Version, remote: &Version, preview_channel: bool) -> bool {
    remote.cmp_precedence(current).is_gt() && (preview_channel || remote.pre.is_empty())
}

// Inputs have already passed the installed version and channel checks.
pub(super) fn select(
    stable: Option<&str>,
    preview: Option<&str>,
    allow_preview: bool,
) -> Result<Choice, String> {
    match (stable, preview, allow_preview) {
        (Some(stable), Some(preview), true) => {
            let parse = |version| {
                Version::parse(version).map_err(|_| "Invalid release version.".to_owned())
            };
            if parse(preview)?.cmp_precedence(&parse(stable)?).is_gt() {
                Ok(Choice::Preview)
            } else {
                Ok(Choice::Stable)
            }
        }
        (Some(_), _, _) => Ok(Choice::Stable),
        (None, Some(_), true) => Ok(Choice::Preview),
        (None, Some(_), false) => Ok(Choice::PreviewNotice),
        (None, None, _) => Ok(Choice::Current),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stable_only_notices_preview_without_authorizing_install() {
        assert_eq!(
            select(None, Some("0.1.0-rc.6"), false).unwrap(),
            Choice::PreviewNotice
        );
        assert_eq!(
            select(Some("1.0.0"), Some("1.1.0-rc.6"), false).unwrap(),
            Choice::Stable
        );
        assert_eq!(select(None, None, false).unwrap(), Choice::Current);
    }

    #[test]
    fn opted_in_uses_semantic_precedence() {
        assert_eq!(
            select(None, Some("1.1.0-rc.1"), true).unwrap(),
            Choice::Preview
        );
        for preview in ["1.9.0-rc.10", "1.10.0-rc.99", "1.10.0+2"] {
            assert_eq!(
                select(Some("1.10.0"), Some(preview), true).unwrap(),
                Choice::Stable
            );
        }
        assert_eq!(
            select(Some("1.0.0"), Some("1.1.0-rc.1"), true).unwrap(),
            Choice::Preview
        );
    }

    #[test]
    fn installed_version_filters_old_equal_and_wrong_channel() {
        let installed = semver::Version::parse("1.0.0-rc.10+abc").unwrap();
        let eligible =
            |v, preview| eligible_version(&installed, &semver::Version::parse(v).unwrap(), preview);
        assert!(!eligible("1.0.0-rc.2", true));
        assert!(!eligible("1.0.0-rc.10+new", true));
        assert!(!eligible("1.0.0-rc.11", false));
        assert!(eligible("1.0.0-rc.11", true));
        assert!(eligible("1.0.0", false));
    }
}

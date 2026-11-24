from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from updater_assets import signed_archive


class MacArchiveTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.bundle = Path(tmp.name)
        (self.bundle / 'macos').mkdir()
        self.archive = self.bundle / 'macos/HuntWick.app.tar.gz'
        self.pattern = 'macos/*.app.tar.gz'

    def test_dmg_is_not_an_updater_archive(self):
        (self.bundle / 'HuntWick.dmg').touch()
        with self.assertRaisesRegex(ValueError, 'found 0'):
            signed_archive(self.bundle, self.pattern)

    def test_missing_and_empty_signatures(self):
        self.archive.touch()
        with self.assertRaisesRegex(ValueError, 'Missing Tauri signature'):
            signed_archive(self.bundle, self.pattern)
        Path(str(self.archive) + '.sig').write_text(' ')
        with self.assertRaisesRegex(ValueError, 'Missing Tauri signature'):
            signed_archive(self.bundle, self.pattern)

    def test_unique_signed_bundle(self):
        self.archive.touch()
        Path(str(self.archive) + '.sig').write_text('fixture')
        self.assertEqual(signed_archive(self.bundle, self.pattern), self.archive)
        (self.bundle / 'macos/Stale.app.tar.gz').touch()
        with self.assertRaisesRegex(ValueError, 'found 2'):
            signed_archive(self.bundle, self.pattern)

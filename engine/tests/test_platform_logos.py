"""Catalog drift, artist attribution and local asset checks run offline in engine CI."""
import csv
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/platform_logos'))
import registry


class PlatformLogoTests(unittest.TestCase):
    def test_generated_artwork_and_directory_match_the_current_engine(self):
        for path, expected in registry.artifacts().items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_text(encoding='utf-8'), expected,
                                 'Regenerate with python scripts/platform_logos/registry.py')

    def test_all_audited_names_match_runtime_lookups(self):
        mappings = json.loads((registry.ROOT/'src/platformLogos.generated.json').read_text(encoding='utf-8'))
        with (registry.ROOT/'docs/platform-logos/catalog.csv').open(encoding='utf-8', newline='') as file:
            for row in csv.DictReader(file):
                name = row['platform']
                slug = mappings['instances'].get(name.strip().lower(),
                            mappings['brands'].get(registry.normalized(name), ''))
                self.assertEqual(row['logo'],slug,name)

    def test_invalid_svg_is_rejected(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'invalid.svg'
            for content in ['<svg></svg>', '<svg xmlns="http://www.w3.org/2000/svg" '
                            'viewBox="0 0 24 24"><path d="M0 0"/><script/></svg>']:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    registry.check_art(path)

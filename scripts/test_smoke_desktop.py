import unittest

from smoke_desktop import desktop_environment


class DesktopEnvironmentTests(unittest.TestCase):
    def test_windows_key_casing_and_system_only_path(self):
        root = r"D:\Windows"
        for key in ("SYSTEMROOT", "SystemRoot", "systemroot"):
            with self.subTest(key=key):
                source = {key: root, "Path": r"C:\Python", "Temp": "tmp",
                          "PythonHome": "bad", "PythonPath": "bad", "virtual_env": "bad"}
                self.assertEqual(desktop_environment(source, True), {
                    "SYSTEMROOT": root, "TEMP": "tmp", "PATH": root + r"\System32;" + root})

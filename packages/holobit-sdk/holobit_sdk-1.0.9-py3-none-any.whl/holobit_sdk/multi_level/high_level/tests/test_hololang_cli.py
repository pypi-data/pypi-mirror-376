import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestHoloLangCLI(unittest.TestCase):
    def test_cli_inline(self):
        cmd = [
            sys.executable,
            "-m",
            "holobit_sdk.multi_level.high_level.hololang_cli",
            "-c",
            "CREAR H1 (0.1, 0.2, 0.3)",
            "-c",
            "IMPRIMIR H1",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.assertIn("Variable H1 creada", result.stdout)
        self.assertIn("H1 = (0.1, 0.2, 0.3)", result.stdout)

    def test_cli_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".holo") as tmp:
            tmp.write("CREAR H2 (0.4, 0.5, 0.6)\nIMPRIMIR H2\n")
            tmp_path = Path(tmp.name)
        cmd = [
            sys.executable,
            "-m",
            "holobit_sdk.multi_level.high_level.hololang_cli",
            "--file",
            str(tmp_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.assertIn("Variable H2 creada", result.stdout)
        self.assertIn("H2 = (0.4, 0.5, 0.6)", result.stdout)
        tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()

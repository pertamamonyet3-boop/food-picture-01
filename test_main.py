"""Tests for the food picture entrypoint, using disposable image-like bytes."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import main

MAIN = Path(__file__).resolve().with_name("main.py")


class EntryTests(unittest.TestCase):
    def run_entry(self, source_dir: Path, cwd: Path, output: Path):
        env = os.environ.copy()
        env["MAKEFUN_OUTPUT_DIR"] = str(output)
        return subprocess.run([sys.executable, str(source_dir / "main.py")], cwd=cwd, env=env, capture_output=True)

    def make_source_dir(self, root: Path) -> Path:
        source_dir = root / "source"
        source_dir.mkdir()
        (source_dir / "main.py").write_bytes(MAIN.read_bytes())
        return source_dir

    def test_repeated_output_is_byte_identical_and_source_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            elsewhere = root / "elsewhere"
            elsewhere.mkdir()
            source_dir = self.make_source_dir(root)
            source = source_dir / "food.jpg"
            fixture = b"\xff\xd8\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xd9"
            source.write_bytes(fixture)
            try:
                out = root / "out"
                first = self.run_entry(source_dir, root, out)
                second = self.run_entry(source_dir, elsewhere, out)
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertEqual((out / "entry.png").read_bytes(), fixture)
                self.assertEqual(source.read_bytes(), fixture)
            finally:
                source.unlink(missing_ok=True)

    def test_missing_artwork_has_useful_error_and_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = self.make_source_dir(root)
            out = root / "out"
            result = self.run_entry(source_dir, root, out)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"food.jpg or food.png", result.stderr)
            self.assertFalse(out.exists())

    def test_custom_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = self.make_source_dir(root)
            source = source_dir / "food.png"
            source.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00")
            env = os.environ.copy()
            env.pop("MAKEFUN_OUTPUT_DIR", None)
            env["MAKEFUN_OUTPUT_DIR"] = str(root / "default-out")
            try:
                result = subprocess.run([sys.executable, str(source_dir / "main.py")], cwd=root, env=env, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((root / "default-out" / "entry.png").read_bytes(), source.read_bytes())
            finally:
                source.unlink(missing_ok=True)

    def test_bad_signature_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = self.make_source_dir(root)
            source = source_dir / "food.png"
            source.write_bytes(b"not an image")
            try:
                out = root / "out"
                result = self.run_entry(source_dir, root, out)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"valid PNG header", result.stderr)
                self.assertFalse((out / "entry.png").exists())
            finally:
                source.unlink(missing_ok=True)

    def test_default_output_directory(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(main.output_directory(), Path("/output"))


if __name__ == "__main__":
    unittest.main()

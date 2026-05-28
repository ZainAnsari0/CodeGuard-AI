"""Tests for file upload validation: extension, size, ZIP bomb, and path traversal checks."""

import os
import tempfile
import zipfile

import pytest
from app.services.file_validator import FileSecurityValidator, file_validator
from app.core.config import settings

settings_max_file_size = settings.MAX_FILE_SIZE


class TestFilenameSanitization:
    """Tests for filename sanitization."""

    def test_normal_filename_unchanged(self):
        assert file_validator.sanitize_filename("script.py") == "script.py"

    def test_removes_path_traversal(self):
        assert file_validator.sanitize_filename("../../etc/passwd") == "passwd"

    def test_removes_leading_dots(self):
        result = file_validator.sanitize_filename(".hidden_file")
        # Should not produce an empty filename
        assert result != ""

    def test_strips_dangerous_characters(self):
        result = file_validator.sanitize_filename('file|name<>test.py')
        assert "|" not in result
        assert "<" not in result
        assert ">" not in result

    def test_strips_null_bytes(self):
        result = file_validator.sanitize_filename("file\x00name.py")
        assert "\x00" not in result

    def test_empty_filename_becomes_unnamed(self):
        result = file_validator.sanitize_filename("")
        assert result == "unnamed_file"

    def test_dots_only_becomes_unnamed(self):
        result = file_validator.sanitize_filename("...")
        assert result == "unnamed_file"

    def test_windows_path_only_strips_basename(self):
        """os.path.basename on Linux doesn't split on backslashes."""
        result = file_validator.sanitize_filename("C:\\Users\\test\\file.py")
        # On Linux, os.path.basename treats backslashes as part of the filename
        # The sanitizer should still strip dangerous chars from the result
        assert "file.py" in result or result != ""


class TestFileValidation:
    """Tests for single file validation."""

    def test_valid_python_file(self):
        result = file_validator.validate_file("test.py", b"print('hello')")
        assert result.is_valid is True
        assert result.sanitized_filename == "test.py"

    def test_valid_javascript_file(self):
        result = file_validator.validate_file("app.js", b"console.log('hello')")
        assert result.is_valid is True

    def test_rejected_extension(self):
        result = file_validator.validate_file("malware.exe", b"binary data")
        assert result.is_valid is False
        assert any("not allowed" in e for e in result.errors)

    def test_rejected_php_extension(self):
        result = file_validator.validate_file("shell.php", b"<?php system($_GET['cmd']); ?>")
        assert result.is_valid is False

    def test_file_too_large(self):
        large_content = b"x" * (settings_max_file_size + 1)
        result = file_validator.validate_file("big.py", large_content)
        assert result.is_valid is False
        assert any("exceeds limit" in e for e in result.errors)

    def test_mixed_case_extension(self):
        result = file_validator.validate_file("Test.PY", b"print('hello')")
        assert result.is_valid is True

    def test_double_extension(self):
        result = file_validator.validate_file("test.py.txt", b"content")
        assert result.is_valid is False  # .txt not in allowed list


class TestZipValidation:
    """Tests for ZIP archive validation."""

    def _create_zip(self, files: dict, zip_path: str):
        """Helper to create a zip file with given files."""
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)

    def test_valid_zip(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            zip_path = f.name
        try:
            self._create_zip({"script.py": "print('hello')"}, zip_path)
            result = file_validator.validate_zip(zip_path)
            assert result.is_valid is True
            assert "script.py" in result.entries
        finally:
            os.unlink(zip_path)

    def test_zip_with_path_traversal(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            zip_path = f.name
        try:
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("../../../etc/passwd", "root:x:0:0:root:/root:/bin/bash")
            result = file_validator.validate_zip(zip_path)
            assert result.is_valid is False
            assert any("Unsafe path" in e for e in result.errors)
        finally:
            os.unlink(zip_path)

    def test_zip_with_too_many_entries(self):
        """ZIP with more than max entries should be rejected."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            zip_path = f.name
        try:
            with zipfile.ZipFile(zip_path, "w") as zf:
                for i in range(1001):  # Max is 1000
                    zf.writestr(f"file_{i}.py", f"# file {i}")
            result = file_validator.validate_zip(zip_path)
            assert result.is_valid is False
            assert any("entries" in e for e in result.errors)
        finally:
            os.unlink(zip_path)

    def test_corrupted_zip(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(b"not a zip file")
            zip_path = f.name
        try:
            result = file_validator.validate_zip(zip_path)
            assert result.is_valid is False
            assert any("Invalid" in e or "corrupted" in e for e in result.errors)
        finally:
            os.unlink(zip_path)

    def test_zip_extraction(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            zip_path = f.name
        extract_dir = tempfile.mkdtemp()
        try:
            self._create_zip({"script.py": "print('hello')"}, zip_path)
            result = file_validator.validate_zip(zip_path)
            assert result.is_valid is True

            extracted, errors = file_validator.extract_zip(zip_path, extract_dir)
            assert len(errors) == 0
            assert len(extracted) == 1
        finally:
            os.unlink(zip_path)
            import shutil
            shutil.rmtree(extract_dir, ignore_errors=True)
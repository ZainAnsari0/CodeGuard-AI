"""
CodeGuard AI - File Upload Security Validator
Validates uploaded files for security threats including MIME type checking,
file size limits, ZIP bomb detection, and path traversal prevention.
"""

import logging
import os
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

import magic

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    ".py": {"text/x-python", "text/x-script.python", "application/x-python-code"},
    ".js": {"text/javascript", "application/javascript", "text/x-js"},
    ".ts": {"text/typescript", "application/typescript", "text/x-typescript"},
    ".java": {"text/x-java", "text/x-java-source"},
    ".go": {"text/x-go", "text/go"},
    ".rs": {"text/x-rust", "text/rust"},
    ".c": {"text/x-c", "text/c"},
    ".cpp": {"text/x-c++", "text/c++"},
    ".h": {"text/x-c", "text/c", "text/x-chdr"},
    ".hpp": {"text/x-c++", "text/c++"},
    ".swift": {"text/x-swift"},
    ".zip": {"application/zip", "application/x-zip-compressed"},
}

MAX_ZIP_ENTRIES = 1000
MAX_ZIP_DEPTH = 3
MAX_ZIP_RATIO = 10.0
MAX_ZIP_UNCOMPRESSED_SIZE = 100 * 1024 * 1024  # 100MB


class ValidationResult:
    """Result of file validation."""

    def __init__(self, is_valid: bool, sanitized_filename: str = "",
                 errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None,
                 detected_mime: str = "", file_size: int = 0):
        self.is_valid = is_valid
        self.sanitized_filename = sanitized_filename
        self.errors = errors or []
        self.warnings = warnings or []
        self.detected_mime = detected_mime
        self.file_size = file_size


class ZipValidationResult:
    """Result of ZIP archive validation."""

    def __init__(self, is_valid: bool, entries: Optional[List[str]] = None,
                 total_size: int = 0, errors: Optional[List[str]] = None,
                 warnings: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.entries = entries or []
        self.total_size = total_size
        self.errors = errors or []
        self.warnings = warnings or []


class FileSecurityValidator:
    """Validates uploaded files for security threats."""

    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = [ext.lower() for ext in settings.ALLOWED_EXTENSIONS]
        self.max_zip_entries = MAX_ZIP_ENTRIES
        self.max_zip_depth = MAX_ZIP_DEPTH
        self.max_zip_ratio = MAX_ZIP_RATIO

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks."""
        filename = os.path.basename(filename)
        filename = filename.replace("\x00", "").replace("\r", "").replace("\n", "")
        dangerous_chars = ["..", "~", "|", "<", ">", "*", "?", '"']
        for char in dangerous_chars:
            filename = filename.replace(char, "")
        filename = filename.strip(". ")
        if not filename:
            filename = "unnamed_file"
        return filename

    def detect_mime_type(self, file_content: bytes) -> str:
        """Detect MIME type using python-magic."""
        try:
            return magic.from_buffer(file_content, mime=True)
        except Exception as e:
            logger.warning(f"MIME detection failed: {e}")
            return "application/octet-stream"

    def validate_file(self, filename: str, file_content: bytes) -> ValidationResult:
        """Validate a single file upload.

        Checks: filename safety, extension, size, MIME type.
        """
        errors: List[str] = []
        warnings: List[str] = []

        sanitized = self.sanitize_filename(filename)

        ext = Path(sanitized).suffix.lower()
        if ext not in self.allowed_extensions:
            errors.append(f"File extension '{ext}' is not allowed. Allowed: {', '.join(self.allowed_extensions)}")

        if len(file_content) > self.max_file_size:
            errors.append(f"File size ({len(file_content)} bytes) exceeds limit ({self.max_file_size} bytes)")

        detected_mime = self.detect_mime_type(file_content)
        if ext in ALLOWED_MIME_TYPES and detected_mime not in ALLOWED_MIME_TYPES[ext]:
            if detected_mime.startswith("text/") or detected_mime == "application/octet-stream":
                warnings.append(f"MIME type '{detected_mime}' doesn't match expected for '{ext}', but may be valid")
            else:
                errors.append(f"MIME type '{detected_mime}' not allowed for extension '{ext}'")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_filename=sanitized,
            errors=errors,
            warnings=warnings,
            detected_mime=detected_mime,
            file_size=len(file_content),
        )

    def validate_zip(self, zip_path: str) -> ZipValidationResult:
        """Validate a ZIP archive for security threats.

        Checks: entry count, nesting depth, compression ratio (zip bomb), filename safety.
        """
        errors: List[str] = []
        warnings: List[str] = []
        entries: List[str] = []
        total_uncompressed = 0

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                if len(zf.namelist()) > self.max_zip_entries:
                    errors.append(f"ZIP contains {len(zf.namelist())} entries, max is {self.max_zip_entries}")

                for info in zf.infolist():
                    name = info.filename

                    if name.startswith("/") or ".." in name or "\x00" in name:
                        errors.append(f"Unsafe path in ZIP: {name}")
                        continue

                    depth = name.count("/")
                    if depth > self.max_zip_depth:
                        errors.append(f"ZIP nesting too deep ({depth}): {name}")
                        continue

                    entries.append(name)
                    total_uncompressed += info.file_size

                    if info.file_size > 0 and info.compress_size > 0:
                        ratio = info.file_size / info.compress_size
                        if ratio > self.max_zip_ratio:
                            errors.append(
                                f"Compression ratio too high ({ratio:.1f}x) for {name}: "
                                f"possible zip bomb"
                            )

                if total_uncompressed > MAX_ZIP_UNCOMPRESSED_SIZE:
                    errors.append(
                        f"Total uncompressed size ({total_uncompressed} bytes) "
                        f"exceeds limit ({MAX_ZIP_UNCOMPRESSED_SIZE} bytes)"
                    )

        except zipfile.BadZipFile:
            errors.append("Invalid or corrupted ZIP file")
        except Exception as e:
            errors.append(f"ZIP validation error: {str(e)}")

        return ZipValidationResult(
            is_valid=len(errors) == 0,
            entries=entries,
            total_size=total_uncompressed,
            errors=errors,
            warnings=warnings,
        )

    def extract_zip(self, zip_path: str, extract_dir: str) -> Tuple[List[str], List[str]]:
        """Safely extract a validated ZIP archive.

        Returns: (list of extracted file paths, list of error messages)
        """
        extracted_files: List[str] = []
        errors: List[str] = []

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for info in zf.infolist():
                    name = info.filename
                    if name.startswith("/") or ".." in name:
                        continue

                    target_path = os.path.join(extract_dir, name)

                    # Path traversal protection: verify resolved path stays within extract_dir
                    real_extract = os.path.realpath(extract_dir)
                    real_target = os.path.realpath(target_path)
                    if not real_target.startswith(real_extract + os.sep) and real_target != real_extract:
                        errors.append(f"Path traversal detected: {name}")
                        continue
                    if name.endswith("/"):
                        os.makedirs(target_path, exist_ok=True)
                        continue

                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    ext = Path(name).suffix.lower()
                    if ext not in self.allowed_extensions:
                        warnings_msg = f"Skipping disallowed file: {name}"
                        logger.info(warnings_msg)
                        continue

                    zf.extract(info, extract_dir)
                    extracted_files.append(target_path)

        except Exception as e:
            errors.append(f"ZIP extraction error: {str(e)}")

        return extracted_files, errors


file_validator = FileSecurityValidator()
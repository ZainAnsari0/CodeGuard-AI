import os

ALLOWED_CONFIG_DIR = "/etc/app/configs/"
ALLOWED_TEMPLATE_DIR = "/var/www/templates/"
ALLOWED_UPLOAD_DIR = "/app/uploads/"

def _validate_path(base_dir, filename):
    """Resolve and validate that a path stays within the allowed directory."""
    resolved = os.path.realpath(os.path.join(base_dir, filename))
    if not resolved.startswith(os.path.realpath(base_dir)):
        raise ValueError(f"Path traversal detected: {filename}")
    return resolved

def read_config(filename):
    # SAFE: Path validation prevents traversal
    filepath = _validate_path(ALLOWED_CONFIG_DIR, filename)
    with open(filepath, "r") as f:
        return f.read()

def get_template(template_name):
    # SAFE: Path validation with base directory check
    path = _validate_path(ALLOWED_TEMPLATE_DIR, template_name)
    with open(path, "r") as f:
        return f.read()

def download_file(user_path):
    # SAFE: Path validation prevents traversal outside upload dir
    full_path = _validate_path(ALLOWED_UPLOAD_DIR, user_path)
    with open(full_path, "rb") as f:
        return f.read()
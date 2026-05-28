import os

def read_config(filename):
    # VULNERABLE: Path traversal - user input directly concatenated into file path
    filepath = os.path.join("/etc/app/configs/", filename)
    with open(filepath, "r") as f:
        return f.read()

def get_template(template_name):
    # VULNERABLE: Path traversal via string concatenation
    path = "/var/www/templates/" + template_name
    with open(path, "r") as f:
        return f.read()

def download_file(user_path):
    # VULNERABLE: Path traversal without validation
    full_path = os.path.join("/app/uploads/", user_path)
    with open(full_path, "rb") as f:
        return f.read()
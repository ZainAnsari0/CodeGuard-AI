import os

def get_db_connection():
    # SAFE: Credentials loaded from environment variables
    host = os.environ.get("DB_HOST", "localhost")
    port = int(os.environ.get("DB_PORT", "5432"))
    username = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    database = os.environ.get("DB_NAME")
    if not all([username, password, database]):
        raise ValueError("Database credentials not configured")
    connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    return connection_string

def connect_api():
    # SAFE: API key from environment variable
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise ValueError("API key not configured")
    headers = {"Authorization": f"Bearer {api_key}"}
    return headers

# SAFE: AWS credentials from environment
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
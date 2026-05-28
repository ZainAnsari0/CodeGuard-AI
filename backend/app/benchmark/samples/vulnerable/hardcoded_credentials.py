import os

def get_db_connection():
    # VULNERABLE: Hardcoded database credentials
    host = "prod-db.internal"
    port = 5432
    username = "admin"
    password = "SuperSecret123!"  # Hardcoded password
    database = "production_db"
    connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    return connection_string

def connect_api():
    # VULNERABLE: Hardcoded API key
    api_key = "sk-abc123def456ghi789"  # Hardcoded API key
    headers = {"Authorization": f"Bearer {api_key}"}
    return headers

AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"  # VULNERABLE: Hardcoded AWS key
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # VULNERABLE: Hardcoded secret
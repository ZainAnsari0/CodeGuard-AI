"""Integration test fixtures: authenticated clients, sample files."""

import pytest
import pytest_asyncio
from tests.conftest import test_db, client, test_user, admin_user, auth_headers, admin_headers, mock_ai_chain


@pytest_asyncio.fixture
async def authed_client(client, test_user):
    """Authenticated client with developer role."""
    client.headers.update({"Authorization": f"Bearer {test_user['token']}"})
    return client


@pytest_asyncio.fixture
async def admin_client(client, admin_user):
    """Authenticated client with admin role."""
    client.headers.update({"Authorization": f"Bearer {admin_user['token']}"})
    return client


@pytest.fixture
def sample_python_file():
    """Sample Python file content for upload testing."""
    return b"import os\n\ndef hello():\n    print('Hello, World!')\n"


@pytest.fixture
def sample_js_file():
    """Sample JavaScript file content for upload testing."""
    return b"function hello() {\n    console.log('Hello, World!');\n}\n"
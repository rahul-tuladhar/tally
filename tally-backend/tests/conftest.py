import asyncio
import uuid
from typing import Any

import httpx
import pytest

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test timeout settings
TEST_TIMEOUT = 30.0


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def http_client():
    """Create an HTTP client for making requests to the API."""
    async with httpx.AsyncClient(
        base_url=BASE_URL,
        timeout=TEST_TIMEOUT,
        follow_redirects=True
    ) as client:
        yield client


@pytest.fixture(scope="session")
async def api_client(http_client):
    """API client with base URL set to API endpoints."""
    http_client.base_url = API_BASE
    return http_client


@pytest.fixture
async def test_control_data() -> dict[str, Any]:
    """Test data for creating a control."""
    return {
        "title": f"Test Control {uuid.uuid4().hex[:8]}",
        "description": "A test control for automated testing",
        "prompt": "Does this document meet the test requirements?"
    }


@pytest.fixture
async def created_control(api_client: httpx.AsyncClient, test_control_data: dict[str, Any]) -> dict[str, Any]:
    """Create a test control and return its data."""
    response = await api_client.post("/controls/", json=test_control_data)
    assert response.status_code == 200
    control = response.json()

    yield control

    # Cleanup: Delete the control after test
    try:
        await api_client.delete(f"/controls/{control['id']}")
    except:
        pass  # Ignore cleanup errors


@pytest.fixture
async def test_bucket_name() -> str:
    """Generate a unique test bucket name."""
    return f"test-bucket-{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def created_bucket(api_client: httpx.AsyncClient, test_bucket_name: str) -> dict[str, Any]:
    """Create a test bucket and return its data."""
    response = await api_client.post(
        "/documents/buckets",
        params={
            "bucket_name": test_bucket_name,
            "public": False,
            "file_size_limit": 10485760  # 10MB
        }
    )

    if response.status_code == 409:
        # Bucket already exists, that's fine for testing
        bucket_data = {"bucket_name": test_bucket_name}
    else:
        assert response.status_code == 200
        bucket_data = response.json()

    yield bucket_data

    # Note: We don't cleanup buckets as they might be needed across tests


@pytest.fixture
async def test_file_data() -> dict[str, Any]:
    """Test data for file operations."""
    return {
        "file_name": f"test-document-{uuid.uuid4().hex[:8]}.pdf",
        "content_type": "application/pdf",
        "bucket_name": "tally-documents",
        "user_id": f"test-user-{uuid.uuid4().hex[:8]}"
    }


class DataManager:
    """Helper class to manage test data across multiple tests."""

    def __init__(self):
        self.created_controls = []
        self.created_files = []
        self.created_ai_responses = []

    def add_control(self, control_id: str):
        self.created_controls.append(control_id)

    def add_file(self, file_path: str):
        self.created_files.append(file_path)

    def add_ai_response(self, response_id: str):
        self.created_ai_responses.append(response_id)

    async def cleanup_all(self, api_client: httpx.AsyncClient):
        """Clean up all created test data."""
        # Cleanup AI responses
        for response_id in self.created_ai_responses:
            try:
                # Note: We don't have a delete endpoint for AI responses
                pass
            except:
                pass

        # Cleanup files
        for file_path in self.created_files:
            try:
                await api_client.delete(f"/documents/files/{file_path}")
            except:
                pass

        # Cleanup controls
        for control_id in self.created_controls:
            try:
                await api_client.delete(f"/controls/{control_id}")
            except:
                pass


@pytest.fixture(scope="session")
async def test_data_manager() -> DataManager:
    """Global test data manager for cleanup."""
    return DataManager()


# Removed autouse health_check fixture as it was causing async issues


# Helper functions for tests
async def assert_successful_response(response: httpx.Response, expected_status: int = 200):
    """Assert that a response is successful and return JSON data."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
    return response.json()


async def wait_for_processing(api_client: httpx.AsyncClient, check_endpoint: str, max_attempts: int = 10):
    """Wait for async processing to complete."""
    for _ in range(max_attempts):
        response = await api_client.get(check_endpoint)
        data = await assert_successful_response(response)

        # Check if processing is complete (this depends on the specific endpoint)
        if isinstance(data, dict) and data.get("status") in ["completed", "failed"]:
            return data

        await asyncio.sleep(1)

    raise TimeoutError(f"Processing did not complete within {max_attempts} attempts")

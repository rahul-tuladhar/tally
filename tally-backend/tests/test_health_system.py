import httpx
import pytest


class TestHealthAndSystem:
    """Test health check and system endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test the health check endpoint."""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()

                    # Verify health response structure
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "is_healthy" in data

        # Status should be healthy or degraded
        assert data["status"] in ["healthy", "degraded"]

        # Should have basic checks
        checks = data["checks"]
        assert "database" in checks
        assert "api_server" in checks
        assert "response_time" in checks

        print(f"✅ Health check passed: {data['status']}")

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test the root endpoint returns basic info."""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()

                    # Should return basic application info
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

        print(f"✅ Root endpoint: {data['message']}")

    @pytest.mark.asyncio
    async def test_docs_endpoint_accessible(self):
        """Test that the API documentation is accessible."""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/docs")
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")

            print("✅ API docs accessible")

    @pytest.mark.asyncio
    async def test_openapi_json_accessible(self):
        """Test that the OpenAPI JSON schema is accessible."""
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/openapi.json")
            assert response.status_code == 200
            data = response.json()

            # Should be a valid OpenAPI schema
            assert "openapi" in data
            assert "info" in data
            assert "paths" in data

            print(f"✅ OpenAPI schema accessible: {data['info']['title']}")

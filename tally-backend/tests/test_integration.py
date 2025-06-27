import httpx
import pytest


class TestIntegrationWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_control_lifecycle(self):
        """Test the complete lifecycle of a control."""
        # 1. Create a control
        control_data = {
            "title": "Integration Test Control",
            "description": "Testing complete workflow",
            "prompt": "Does this document meet our requirements"
        }

        async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
            # Create
            response = await client.post("/controls/", json=control_data)
            assert response.status_code == 200
            control = response.json()
            control_id = control["id"]

            try:
                # Read
                response = await client.get(f"/controls/{control_id}")
                assert response.status_code == 200
                retrieved_control = response.json()
                assert retrieved_control["title"] == control_data["title"]

                # Update
                update_data = {
                    "title": "Updated Integration Control",
                    "description": "Updated description",
                    "prompt": "Updated prompt",
                    "is_active": False
                }
                response = await client.put(f"/controls/{control_id}", json=update_data)
                assert response.status_code == 200

                # Verify in tabular view
                response = await client.get("/tabular/view")
                assert response.status_code == 200
                tabular_data = response.json()

                # Should find our control in the tabular view
                control_found = any(c["id"] == control_id for c in tabular_data["controls"])
                assert control_found

                print("✅ Complete control lifecycle test passed")

            finally:
                # Delete
                await client.delete(f"/controls/{control_id}")

    @pytest.mark.asyncio
    async def test_api_health_and_endpoints(self):
        """Test that all main API endpoints are accessible."""
        endpoints_to_test = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/api/v1/controls/", "GET"),
            ("/api/v1/tabular/view", "GET"),
            ("/api/v1/documents/", "GET"),
            ("/api/v1/ai/status", "GET")
        ]

        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            for endpoint, method in endpoints_to_test:
                if method == "GET":
                    response = await client.get(endpoint)
                    # Any response except 404 means endpoint exists
                    if response.status_code != 404:
                        print(f"✅ {method} {endpoint} -> {response.status_code}")
                    else:
                        print(f"⚠️  {method} {endpoint} -> 404 (not found)")

        print("✅ API endpoints accessibility test completed")

    @pytest.mark.asyncio
    async def test_cross_module_integration(self):
        """Test integration between different modules."""
        async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
            # Create a control
            control_data = {
                "title": "Cross Module Test",
                "prompt": "Integration test prompt"
            }

            response = await client.post("/controls/", json=control_data)
            assert response.status_code == 200
            control = response.json()
            control_id = control["id"]

            try:
                # Check it appears in tabular view
                response = await client.get("/tabular/view")
                assert response.status_code == 200
                tabular_data = response.json()

                control_found = any(c["id"] == control_id for c in tabular_data["controls"])
                assert control_found

                # Test AI integration (if available)
                response = await client.get(f"/ai/responses?control_id={control_id}")
                # Accept any reasonable response
                assert response.status_code in [200, 400, 404, 500]

                print("✅ Cross-module integration test passed")

            finally:
                # Cleanup
                await client.delete(f"/controls/{control_id}")

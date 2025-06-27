import httpx
import pytest


class TestTabularView:
    """Test tabular view API endpoints."""

    @pytest.mark.asyncio
    async def test_get_tabular_view(self):
        """Test getting the complete tabular view."""
        async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
            response = await client.get("/tabular/view")
            assert response.status_code == 200
            data = response.json()

            # Verify tabular view response structure
            assert "controls" in data
            assert "documents" in data
            assert "rows" in data
            assert "processing_count" in data

            # Verify data types
            assert isinstance(data["controls"], list)
            assert isinstance(data["documents"], list)
            assert isinstance(data["rows"], list)
            assert isinstance(data["processing_count"], int)

            print(f"✅ Tabular view: {len(data['controls'])} controls, {len(data['documents'])} documents, {len(data['rows'])} rows")

    @pytest.mark.asyncio
    async def test_tabular_view_structure(self):
        """Test that tabular view has the expected structure."""
        async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
            response = await client.get("/tabular/view")
            assert response.status_code == 200
            data = response.json()

            # Check if controls have expected structure (if any exist)
            if data["controls"]:
                control = data["controls"][0]
                assert "id" in control
                assert "title" in control
                assert "is_active" in control

            # Check if documents have expected structure (if any exist)
            if data["documents"]:
                document = data["documents"][0]
                assert "id" in document
                assert "name" in document

            # Check if rows have expected structure (if any exist)
            if data["rows"]:
                row = data["rows"][0]
                assert "control_id" in row
                assert "document_id" in row

            print("✅ Tabular view structure verified")

    @pytest.mark.asyncio
    async def test_tabular_view_with_data(self):
        """Test tabular view with some existing data."""
        # First create a control to ensure there's some data
        control_data = {
            "title": "Test Tabular Control",
            "prompt": "Test tabular prompt"
        }

        async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
            # Create a control
            create_response = await client.post("/controls/", json=control_data)
            assert create_response.status_code == 200
            control = create_response.json()
            control_id = control["id"]

            try:
                # Get tabular view
                response = await client.get("/tabular/view")
                assert response.status_code == 200
                data = response.json()

                # Should now have at least one control
                assert len(data["controls"]) >= 1

                # Find our control
                our_control = next((c for c in data["controls"] if c["id"] == control_id), None)
                assert our_control is not None
                assert our_control["title"] == control_data["title"]

                print(f"✅ Tabular view with data: found our control '{our_control['title']}'")

            finally:
                # Cleanup
                await client.delete(f"/controls/{control_id}")

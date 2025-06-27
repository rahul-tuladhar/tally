import uuid
from datetime import datetime

from app.schemas import (
    ControlCreate,
    ControlResponse,
    ControlUpdate,
    ControlWithDocuments,
)
from app.services.storage_service import storage_service


class ControlService:
    """Service for handling control business logic."""

    def __init__(self):
        self.storage_service = storage_service

    async def create_control(self, control_data: ControlCreate) -> ControlResponse:
        """Create a new audit control."""
        control_id = str(uuid.uuid4())
        now = datetime.utcnow()

        control = ControlResponse(
            id=control_id,
            title=control_data.title,
            description=control_data.description,
            prompt=control_data.prompt,
            is_active=True,
            created_at=now,
            updated_at=now
        )

        # Store control data in Supabase
        await self.storage_service.upsert_metadata(
            bucket="controls",
            path=f"{control_id}/metadata.json",
            metadata=control.model_dump()
        )

        return control

    async def get_control(self, control_id: str) -> ControlResponse | None:
        """Get a control by ID."""
        try:
            metadata = await self.storage_service.get_metadata(
                bucket="controls",
                path=f"{control_id}/metadata.json"
            )
            return ControlResponse.model_validate(metadata)
        except Exception:
            return None

    async def get_control_with_documents(self, control_id: str) -> ControlWithDocuments | None:
        """Get a control with its associated documents."""
        control = await self.get_control(control_id)
        if not control:
            return None

        # List all documents in the control's folder
        documents = await self.storage_service.list_files(
            bucket="controls",
            path=f"{control_id}/documents/"
        )

        return ControlWithDocuments(
            **control.model_dump(),
            documents=[doc for doc in documents if doc]
        )

    async def list_controls(self, include_inactive: bool = False) -> list[ControlResponse]:
        """List all controls."""
        # List all control metadata files
        metadata_files = await self.storage_service.list_files(
            bucket="controls",
            path="*/metadata.json"
        )

        controls = []
        for metadata in metadata_files:
            try:
                control = ControlResponse.model_validate(metadata)
                if include_inactive or control.is_active:
                    controls.append(control)
            except Exception:
                continue

        return sorted(controls, key=lambda x: x.created_at, reverse=True)

    async def update_control(
        self,
        control_id: str,
        control_data: ControlUpdate
    ) -> ControlResponse | None:
        """Update an existing control."""
        control = await self.get_control(control_id)
        if not control:
            return None

        # Update fields if provided
        update_data = control_data.model_dump(exclude_unset=True)
        updated_control = control.model_copy(update=update_data)
        updated_control.updated_at = datetime.utcnow()

        # Store updated control data
        await self.storage_service.upsert_metadata(
            bucket="controls",
            path=f"{control_id}/metadata.json",
            metadata=updated_control.model_dump()
        )

        return updated_control

    async def delete_control(self, control_id: str) -> bool:
        """Delete a control and all associated data."""
        try:
            # Delete all files in the control's folder
            await self.storage_service.delete_folder(
                bucket="controls",
                path=f"{control_id}/"
            )
            return True
        except Exception:
            return False

    async def set_control_status(self, control_id: str, is_active: bool) -> bool:
        """Activate or deactivate a control."""
        control = await self.get_control(control_id)
        if not control:
            return False

        control.is_active = is_active
        control.updated_at = datetime.utcnow()

        await self.storage_service.upsert_metadata(
            bucket="controls",
            path=f"{control_id}/metadata.json",
            metadata=control.model_dump()
        )

        return True

    async def get_active_controls(self) -> list[ControlResponse]:
        """Get all active controls."""
        return await self.list_controls(include_inactive=False)

    async def search_controls(self, query: str) -> list[ControlResponse]:
        """Search controls by title or description."""
        controls = await self.list_controls(include_inactive=True)
        query = query.lower()

        return [
            control for control in controls
            if (query in control.title.lower() or
                query in control.description.lower() or
                query in control.prompt.lower()) and
            control.is_active
        ]

    async def duplicate_control(self, control_id: str) -> ControlResponse | None:
        """Create a duplicate of an existing control."""
        original_control = await self.get_control(control_id)
        if not original_control:
            return None

        # Create new control with similar data
        new_control_data = ControlCreate(
            title=f"{original_control.title} (Copy)",
            description=original_control.description,
            prompt=original_control.prompt
        )

        return await self.create_control(new_control_data)

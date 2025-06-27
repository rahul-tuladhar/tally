from typing import Any

from app.modules.controls.service import ControlService
from app.schemas import (
    CellResponse,
    ControlResponse,
    DocumentResponse,
    ProcessingStatus,
    TableRow,
    TabularViewResponse,
)
from app.services.storage_service import storage_service


class TabularService:
    """Service for building tabular view data."""

    def __init__(self):
        self.storage_service = storage_service
        self.control_service = ControlService()

    async def get_tabular_view(self) -> TabularViewResponse:
        """Build complete tabular view with all data."""

        # Get all active controls
        controls = await self.control_service.get_active_controls()

        # Get all documents
        documents = await self.storage_service.list_files(
            bucket="documents",
            path="*"
        )
        documents = sorted(documents, key=lambda x: x.get('created_at', ''), reverse=True)

        # Get all AI responses
        ai_responses = await self.storage_service.list_files(
            bucket="ai_responses",
            path="*"
        )

        # Create response mapping for quick lookup
        response_map: dict[str, Any] = {}
        for response in ai_responses:
            key = f"{response.get('document_id')}_{response.get('control_id')}"
            response_map[key] = response

        # Build table rows
        rows = []
        processing_count = 0

        for document in documents:
            cells = []
            for control in controls:
                key = f"{document.get('id')}_{control.id}"
                response = response_map.get(key)

                if response:
                    status = response.get('status', ProcessingStatus.PENDING)
                    if ProcessingStatus.is_active_status(status):
                        processing_count += 1

                    cells.append(
                        CellResponse(
                            control_id=control.id,
                            document_id=document.get('id'),
                            status=status,
                            confidence=response.get('confidence'),
                            result=response.get('result'),
                            error_message=response.get('error_message')
                        )
                    )
                else:
                    cells.append(
                        CellResponse(
                            control_id=control.id,
                            document_id=document.get('id'),
                            status=ProcessingStatus.PENDING
                        )
                    )

            rows.append(
                TableRow(
                    document=DocumentResponse.model_validate(document),
                    cells=cells
                )
            )

        return TabularViewResponse(
            controls=[ControlResponse.model_validate(control) for control in controls],
            rows=rows,
            processing_count=processing_count
        )

    async def get_processing_status(self) -> dict[str, Any]:
        """Get current processing status summary."""

        # Get all AI responses
        ai_responses = await self.storage_service.list_files(
            bucket="ai_responses",
            path="*"
        )

        # Count responses by status
        status_counts = {status.value: 0 for status in ProcessingStatus}
        for response in ai_responses:
            status = response.get('status')
            if status in status_counts:
                status_counts[status] += 1

        # Count total possible combinations
        controls = await self.control_service.list_controls()
        documents = await self.storage_service.list_files(bucket="documents", path="*")

        total_possible = len(controls) * len(documents)
        total_processed = len(ai_responses)

        processing_count = (
            status_counts.get(ProcessingStatus.PENDING.value, 0) +
            status_counts.get(ProcessingStatus.PROCESSING.value, 0) +
            status_counts.get(ProcessingStatus.REGENERATING.value, 0)
        )

        return {
            "total_possible_combinations": total_possible,
            "total_processed": total_processed,
            "currently_processing": processing_count,
            "status_breakdown": status_counts,
            "completion_percentage": (
                (total_processed / total_possible * 100) if total_possible > 0 else 0
            )
        }

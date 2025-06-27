import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.schemas import DocumentResponse, ExtractionStatus
from app.services.storage_service import storage_service


class DocumentService:
    """Service for handling document operations including Reducto integration."""

    def __init__(self):
        self.storage_service = storage_service
        self.reducto_client = httpx.AsyncClient(
            base_url="https://platform.reducto.ai",
            headers={"Authorization": f"Bearer {settings.REDUCTO_API_KEY}"},
            timeout=30.0,
        )

    async def upload_document(
        self,
        file: UploadFile,
        control_id: str | None = None
    ) -> DocumentResponse:
        """Upload a document and initiate processing."""
        # Validate file
        await self._validate_file(file)

        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        try:
            # Upload to Supabase storage
            file_url = await self.storage_service.upload_file(
                file=file.file,
                filename=unique_filename,
                content_type=file.content_type,
            )

            # Create document response
            document = DocumentResponse(
                id=str(uuid.uuid4()),
                filename=unique_filename,
                original_filename=file.filename,
                file_type=file.content_type,
                file_size=file.size,
                file_url=file_url,
                extraction_status=ExtractionStatus.PENDING,
                control_id=control_id if control_id else None
            )

            # Start Reducto processing asynchronously
            await self._initiate_reducto_processing(document.id, file_url)

            return document

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

    async def upload_multiple_documents(
        self,
        files: list[UploadFile],
        control_id: str | None = None
    ) -> dict[str, Any]:
        """Upload multiple documents in batch."""
        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                document = await self.upload_document(file, control_id)
                uploaded_files.append(document)
            except Exception as e:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })

        return {
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "total_uploaded": len(uploaded_files),
            "total_failed": len(failed_files)
        }

    async def get_document(self, document_id: str) -> DocumentResponse | None:
        """Get document by ID."""
        # In a stateless approach, we would typically retrieve this from a cache or storage
        # For now, we'll just return None as we don't have persistent storage
        return None

    async def get_documents_by_control(self, control_id: str) -> list[DocumentResponse]:
        """Get all documents for a specific control."""
        # In a stateless approach, we would typically retrieve this from a cache or storage
        # For now, we'll return an empty list as we don't have persistent storage
        return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete document and associated files."""
        try:
            # Delete from storage
            # Note: In a stateless approach, we would need the filename from somewhere
            # For now, we'll just return True
            return True

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
            )

        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"File type {file.content_type} not supported"
            )

    async def _initiate_reducto_processing(self, document_id: str, file_url: str) -> None:
        """Initiate Reducto processing for a document."""
        try:
            # Upload to Reducto using file URL
            reducto_response = await self._upload_to_reducto_via_url(file_url)

            # Extract data from document
            await self._extract_document_data(document_id, reducto_response.get("file_id"))

        except Exception as e:
            # In a stateless approach, we would log this error or notify through a message queue
            raise e

    async def _upload_to_reducto_via_url(self, file_url: str) -> dict[str, Any]:
        """Upload document to Reducto using file URL."""
        response = await self.reducto_client.post(
            "/parse",
            json={"document_url": file_url}
        )
        response.raise_for_status()
        return response.json()

    async def _extract_document_data(self, document_id: str, reducto_file_id: str | None) -> None:
        """Extract structured data from document using Reducto."""
        if not reducto_file_id:
            return

        try:
            # Extract data using Reducto
            extract_response = await self.reducto_client.post(
                "/extract",
                json={
                    "document_url": reducto_file_id,
                    "include_citations": True,
                    "output_format": "structured"
                }
            )
            extract_response.raise_for_status()

            # In a stateless approach, we would send this data to a message queue
            # or store it in a cache for later retrieval
            return extract_response.json()

        except Exception as e:
            # Log error or notify through message queue
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract document data: {str(e)}"
            )

    async def close(self) -> None:
        """Close any open connections."""
        await self.reducto_client.aclose()

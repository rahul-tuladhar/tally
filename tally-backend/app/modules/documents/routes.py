from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi_utils.cbv import cbv

from app.schemas import (
    BatchUploadResponse,
    BucketInfoResponse,
    DefaultResponse,
    DocumentResponse,
    DocumentUploadResponse,
    FileMetadataResponse,
    PresignedUrlResponse,
)
from app.services.document_service import DocumentService
from app.services.storage_service import storage_service

router = APIRouter()
document_service = DocumentService()


@cbv(router)
class DocumentRouter:
    @router.post("/upload", response_model=DocumentUploadResponse)
    async def upload_document(
        self,
        file: UploadFile = File(...),
        control_id: str | None = Query(None, description="Optional control ID to associate with the document")
    ) -> DocumentUploadResponse:
        """Upload a document for processing."""
        return await document_service.upload_document(file, control_id)

    @router.post("/upload/batch", response_model=BatchUploadResponse)
    async def upload_multiple_documents(
        self,
        files: list[UploadFile] = File(...),
        control_id: str | None = Query(None, description="Optional control ID to associate with the documents")
    ) -> BatchUploadResponse:
        """Upload multiple documents in batch."""
        result = await document_service.upload_multiple_documents(files, control_id)
        return BatchUploadResponse(**result)

    @router.get("/{document_id}", response_model=DocumentResponse)
    async def get_document(self, document_id: str) -> DocumentResponse:
        """Get document details by ID."""
        document = await document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    @router.get("/", response_model=list[DocumentResponse])
    async def list_documents(
        self,
        control_id: str | None = Query(None, description="Optional control ID to filter documents")
    ) -> list[DocumentResponse]:
        """List documents, optionally filtered by control ID."""
        if control_id:
            return await document_service.get_documents_by_control(control_id)
        return []  # In stateless approach, we would implement this with a cache or storage service

    @router.delete("/{document_id}")
    async def delete_document(self, document_id: str) -> dict:
        """Delete a document by ID."""
        success = await document_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}

    @router.get("/health", response_model=dict)
    async def storage_health(self):
        """Check Supabase Storage connection health"""
        try:
            connection_status = await storage_service.verify_connection()
            return {
                "status": "healthy" if connection_status["connected"] else "unhealthy",
                **connection_status
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Storage health check failed: {str(e)}")

    @router.get("/buckets", response_model=list[BucketInfoResponse])
    async def list_buckets(self):
        """List all available storage buckets"""
        try:
            buckets = await storage_service.list_buckets()
            return buckets
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list buckets: {str(e)}")

    @router.post("/buckets", response_model=dict)
    async def create_bucket(
        self,
        bucket_name: str = Query(..., description="Name of the bucket to create"),
        public: bool = Query(False, description="Whether the bucket should be public"),
        file_size_limit: int | None = Query(None, description="Maximum file size in bytes")
    ):
        """Create a new storage bucket"""
        try:
            result = await storage_service.create_bucket(
                bucket_name=bucket_name,
                public=public,
                file_size_limit=file_size_limit
            )

            if not result["success"]:
                if result.get("error_type") == "bucket_exists":
                    raise HTTPException(status_code=409, detail=result["error"])
                else:
                    raise HTTPException(status_code=400, detail=result["error"])

            return result

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create bucket: {str(e)}")

    @router.post("/upload-url", response_model=PresignedUrlResponse)
    async def generate_upload_url(
        self,
        file_name: str = Query(..., description="Name of the file to upload"),
        content_type: str = Query(..., description="MIME type of the file"),
        bucket_name: str = Query("tally-documents", description="Target bucket name"),
        user_id: str | None = Query(None, description="Optional user ID for file organization")
    ):
        """Generate a presigned URL for file upload"""
        try:
            upload_response = await storage_service.generate_presigned_upload_url(
                file_name=file_name,
                content_type=content_type,
                bucket_name=bucket_name,
                user_id=user_id
            )
            return upload_response

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")

    @router.get("/download-url")
    async def generate_download_url(
        self,
        file_path: str = Query(..., description="Path to the file in storage"),
        bucket_name: str = Query("tally-documents", description="Bucket name"),
        expires_in: int = Query(3600, description="URL expiration time in seconds")
    ):
        """Generate a presigned URL for file download"""
        try:
            download_url = await storage_service.generate_presigned_download_url(
                file_path=file_path,
                bucket_name=bucket_name,
                expires_in=expires_in
            )
            return {
                "download_url": download_url,
                "expires_in": expires_in,
                "file_path": file_path
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

    @router.get("/files", response_model=list[FileMetadataResponse])
    async def list_files(
        self,
        bucket_name: str = Query("tally-documents", description="Bucket name"),
        path: str = Query("", description="Path within bucket"),
        limit: int = Query(100, description="Maximum number of files to return")
    ):
        """List files in a bucket or path"""
        try:
            files = await storage_service.list_files(
                path=path,
                bucket_name=bucket_name,
                limit=limit
            )
            return files

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

    @router.get("/files/{file_path:path}", response_model=FileMetadataResponse)
    async def get_file_metadata(
        self,
        file_path: str,
        bucket_name: str = Query("tally-documents", description="Bucket name")
    ):
        """Get metadata for a specific file"""
        try:
            metadata = await storage_service.get_file_metadata(
                file_path=file_path,
                bucket_name=bucket_name
            )

            if not metadata:
                raise HTTPException(status_code=404, detail="File not found")

            return metadata

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")

    @router.delete("/files/{file_path:path}")
    async def delete_file(
        self,
        file_path: str,
        bucket_name: str = Query("tally-documents", description="Bucket name")
    ):
        """Delete a file from storage"""
        try:
            success = await storage_service.delete_file(
                file_path=file_path,
                bucket_name=bucket_name
            )

            if not success:
                raise HTTPException(status_code=404, detail="File not found or already deleted")

            return DefaultResponse(
                status=True,
                message=f"File '{file_path}' deleted successfully"
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    @router.get("/test-workflow")
    async def test_upload_workflow(self):
        """Test the complete upload workflow"""
        try:
            # 1. Check connection
            health = await storage_service.verify_connection()
            if not health["connected"]:
                return {
                    "step": "connection_failed",
                    "error": health.get("error", "Unknown connection error")
                }

            # 2. Ensure bucket exists
            bucket_name = "tally-documents"
            bucket_result = await storage_service.create_bucket(bucket_name)

            # 3. Generate upload URL for a test PDF
            upload_response = await storage_service.generate_presigned_upload_url(
                file_name="test-document.pdf",
                content_type="application/pdf"
            )

            return {
                "step": "success",
                "message": "Upload workflow test completed successfully",
                "connection": health,
                "bucket": bucket_result,
                "upload_url": upload_response.dict()
            }

        except Exception as e:
            return {
                "step": "error",
                "error": str(e)
            }

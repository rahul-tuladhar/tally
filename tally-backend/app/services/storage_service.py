"""
Supabase Storage Service

This service handles all interactions with Supabase Storage including:
- Bucket creation and management
- Presigned URL generation for uploads/downloads
- File metadata tracking
- Access control validation
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from supabase import AsyncClient, acreate_client
from supabase.lib.client_options import AsyncClientOptions

from app.config import settings


class BucketInfo(BaseModel):
    """Bucket information model"""
    id: str
    name: str
    public: bool
    created_at: datetime
    file_size_limit: int | None = None
    allowed_mime_types: list[str] | None = None


class PresignedUrlResponse(BaseModel):
    """Response model for presigned URL generation"""
    upload_url: str
    file_path: str
    expires_at: datetime
    bucket_name: str
    max_file_size: int


class FileMetadata(BaseModel):
    """File metadata model"""
    name: str
    size: int
    content_type: str
    path: str
    bucket: str
    uploaded_at: datetime
    uploaded_by: str | None = None


class SupabaseStorageService:
    """Service for managing Supabase Storage operations"""

    def __init__(self):
        """Initialize service (client will be created asynchronously)"""
        self.client: AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize Supabase client asynchronously"""
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be configured")

        if self.client is None:
            self.client = await acreate_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY,
                options=AsyncClientOptions(
                    postgrest_client_timeout=10,
                    storage_client_timeout=10
                )
            )

    async def _ensure_client(self) -> None:
        """Ensure client is initialized"""
        if self.client is None:
            await self.initialize()

    async def verify_connection(self) -> dict[str, Any]:
        """Verify connection to Supabase Storage"""
        try:
            await self._ensure_client()
            # Get list of buckets to test connection
            response = await self.client.storage.list_buckets()
            return {
                "connected": True,
                "buckets_count": len(response),
                "buckets": [bucket.name for bucket in response] if response else []
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

    async def create_bucket(
        self,
        bucket_name: str = settings.DEFAULT_BUCKET_NAME,
        public: bool = False,
        file_size_limit: int | None = settings.UPLOAD_MAX_SIZE,
        allowed_mime_types: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Create a new storage bucket
        
        Args:
            bucket_name: Name of the bucket to create
            public: Whether bucket should be public (default: False for privacy)
            file_size_limit: Maximum file size in bytes
            allowed_mime_types: List of allowed MIME types
        
        Returns:
            Dict with creation status and bucket info
        """
        try:
            await self._ensure_client()
            # Prepare bucket options
            options = {
                "public": public
            }

            # Add file restrictions if specified
            if file_size_limit:
                options["fileSizeLimit"] = file_size_limit

            if allowed_mime_types:
                options["allowedMimeTypes"] = allowed_mime_types

            # Create the bucket
            response = await self.client.storage.create_bucket(bucket_name, options)

            return {
                "success": True,
                "bucket_name": bucket_name,
                "message": f"Bucket '{bucket_name}' created successfully",
                "bucket_info": {
                    "name": bucket_name,
                    "public": public,
                    "file_size_limit": file_size_limit,
                    "allowed_mime_types": allowed_mime_types or settings.ALLOWED_FILE_TYPES
                }
            }

        except Exception as e:
            error_message = str(e)

            # Handle specific error cases
            if "already exists" in error_message.lower():
                return {
                    "success": False,
                    "error": f"Bucket '{bucket_name}' already exists",
                    "error_type": "bucket_exists"
                }

            return {
                "success": False,
                "error": f"Failed to create bucket: {error_message}",
                "error_type": "creation_failed"
            }

    async def list_buckets(self) -> list[BucketInfo]:
        """List all available buckets"""
        try:
            await self._ensure_client()
            buckets = await self.client.storage.list_buckets()
            bucket_info_list = []
            for bucket in buckets:
                bucket_info_list.append(BucketInfo(
                    id=bucket.id,
                    name=bucket.name,
                    public=bucket.public,
                    created_at=bucket.created_at,
                    file_size_limit=getattr(bucket, 'file_size_limit', None),
                    allowed_mime_types=getattr(bucket, 'allowed_mime_types', None)
                ))

            return bucket_info_list

        except Exception as e:
            raise Exception(f"Failed to list buckets: {str(e)}")

    async def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists"""
        try:
            buckets = await self.list_buckets()
            return any(bucket.name == bucket_name for bucket in buckets)
        except:
            return False

    async def generate_presigned_upload_url(
        self,
        file_name: str,
        content_type: str,
        bucket_name: str = settings.DEFAULT_BUCKET_NAME,
        expires_in: int = settings.PRESIGNED_URL_EXPIRY,
        user_id: str | None = None
    ) -> PresignedUrlResponse:
        """
        Generate a presigned URL for file upload
        
        Args:
            file_name: Name of the file to upload
            content_type: MIME type of the file
            bucket_name: Target bucket name
            expires_in: URL expiration time in seconds
            user_id: Optional user ID for organizing files
        
        Returns:
            PresignedUrlResponse with upload URL and metadata
        """
        try:
            await self._ensure_client()
            # Validate content type
            if content_type not in settings.ALLOWED_FILE_TYPES:
                raise ValueError(f"File type '{content_type}' is not allowed")

            # Ensure bucket exists
            if not await self.bucket_exists(bucket_name):
                raise ValueError(f"Bucket '{bucket_name}' does not exist")

            # Generate unique file path
            file_id = str(uuid.uuid4())
            file_extension = Path(file_name).suffix

            # Organize by user if provided, otherwise use general uploads folder
            if user_id:
                file_path = f"uploads/{user_id}/{file_id}{file_extension}"
            else:
                file_path = f"uploads/general/{file_id}{file_extension}"

            # Create presigned URL for upload
            response = await self.client.storage.from_(bucket_name).create_signed_upload_url(file_path)

            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            return PresignedUrlResponse(
                upload_url=response['signedURL'],
                file_path=file_path,
                expires_at=expires_at,
                bucket_name=bucket_name,
                max_file_size=settings.UPLOAD_MAX_SIZE
            )

        except Exception as e:
            raise Exception(f"Failed to generate presigned upload URL: {str(e)}")

    async def generate_presigned_download_url(
        self,
        file_path: str,
        bucket_name: str = settings.DEFAULT_BUCKET_NAME,
        expires_in: int = settings.PRESIGNED_URL_EXPIRY
    ) -> str:
        """Generate a presigned URL for file download"""
        try:
            await self._ensure_client()
            response = await self.client.storage.from_(bucket_name).create_signed_url(
                file_path,
                expires_in
            )
            return response['signedURL']

        except Exception as e:
            raise Exception(f"Failed to generate presigned download URL: {str(e)}")

    async def get_file_metadata(
        self,
        file_path: str,
        bucket_name: str = settings.DEFAULT_BUCKET_NAME
    ) -> FileMetadata | None:
        """Get metadata for a specific file"""
        try:
            await self._ensure_client()
            # List files in the bucket to find our file
            file_list = await self.client.storage.from_(bucket_name).list(
                path=str(Path(file_path).parent),
                limit=1000
            )

            # Find the specific file
            for file_info in file_list:
                if file_info['name'] == Path(file_path).name:
                    return FileMetadata(
                        name=file_info['name'],
                        size=file_info.get('size', 0),
                        content_type=file_info.get('content_type', 'application/octet-stream'),
                        path=file_path,
                        bucket=bucket_name,
                        uploaded_at=datetime.fromisoformat(file_info['created_at'].replace('Z', '+00:00')),
                        uploaded_by=file_info.get('owner', None)
                    )

            return None

        except Exception as e:
            raise Exception(f"Failed to get file metadata: {str(e)}")

    async def delete_file(
        self,
        file_path: str,
        bucket_name: str = settings.DEFAULT_BUCKET_NAME
    ) -> bool:
        """Delete a file from storage"""
        try:
            await self._ensure_client()
            response = await self.client.storage.from_(bucket_name).remove([file_path])
            return len(response) > 0

        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")

    async def list_files(
        self,
        path: str = "",
        bucket_name: str = settings.DEFAULT_BUCKET_NAME,
        limit: int = 100
    ) -> list[FileMetadata]:
        """List files in a bucket or path"""
        try:
            await self._ensure_client()
            file_list = await self.client.storage.from_(bucket_name).list(
                path=path,
                limit=limit
            )

            files = []
            for file_info in file_list:
                if file_info.get('name'):  # Skip directories
                    files.append(FileMetadata(
                        name=file_info['name'],
                        size=file_info.get('size', 0),
                        content_type=file_info.get('content_type', 'application/octet-stream'),
                        path=f"{path}/{file_info['name']}" if path else file_info['name'],
                        bucket=bucket_name,
                        uploaded_at=datetime.fromisoformat(file_info['created_at'].replace('Z', '+00:00')),
                        uploaded_by=file_info.get('owner', None)
                    ))

            return files

        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")


# Create a global instance
storage_service = SupabaseStorageService()

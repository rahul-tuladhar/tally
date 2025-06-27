from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    computed_field,
    field_validator,
    model_validator,
)

# Type aliases for better reusability and clarity
PositiveInt = Annotated[int, Field(gt=0, description="Must be a positive integer")]
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
OptionalNonEmptyStr = Annotated[str | None, StringConstraints(min_length=1, strip_whitespace=True)]
FileName = Annotated[str, StringConstraints(min_length=1, max_length=255, pattern=r'^[^<>:"/\\|?*\x00-\x1f]+$')]
ControlTitle = Annotated[str, StringConstraints(min_length=1, max_length=255, strip_whitespace=True)]
ConfidenceScore = Annotated[float, Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")]
UUIDStr = Annotated[str, Field(description="UUID string identifier")]
OptionalPositiveInt = Annotated[int | None, Field(ge=0, description="Must be a positive integer or None")]
NonNegativeInt = Annotated[int, Field(ge=0, description="Must be a non-negative integer")]


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        # Enable validation from SQLAlchemy models
        from_attributes=True,
        # Validate fields when they're assigned (not just on creation)
        validate_assignment=True,
        # Allow arbitrary types (useful for custom types)
        arbitrary_types_allowed=True,
        # Strip whitespace from strings
        str_strip_whitespace=True,
        # Use enum values instead of enum objects in serialization
        use_enum_values=True,
        # Validate default values
        validate_default=True,
        # Strict mode for better type safety (can be overridden per field)
        strict=False,
        # Forbid extra fields by default (can be overridden)
        extra='forbid'
    )


class ProcessingStatus(str, Enum):
    """Status enum for various processing states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REGENERATING = "regenerating"

    @classmethod
    def is_terminal_status(cls, status: "ProcessingStatus") -> bool:
        """Check if status indicates processing is complete (success or failure)."""
        return status in {cls.COMPLETED, cls.FAILED}

    @classmethod
    def is_active_status(cls, status: "ProcessingStatus") -> bool:
        """Check if status indicates active processing."""
        return status in {cls.PROCESSING, cls.REGENERATING}


class ExtractionStatus(str, Enum):
    """Status enum for document extraction."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def is_ready_for_ai_processing(cls, status: "ExtractionStatus") -> bool:
        """Check if extraction is complete and ready for AI processing."""
        return status == cls.COMPLETED


# Control Schemas
class ControlBase(BaseSchema):
    title: ControlTitle = Field(..., description="Control title")
    description: OptionalNonEmptyStr = Field(None, description="Optional control description")
    prompt: NonEmptyStr = Field(..., description="The question/prompt for this control")

    @field_validator('prompt')
    @classmethod
    def validate_prompt_format(cls, v: str) -> str:
        """Ensure prompt is properly formatted."""
        v = v.strip()
        if not v.endswith(('?', '.', '!')):
            v += '?'
        return v

    @model_validator(mode='after')
    def validate_title_prompt_consistency(self) -> 'ControlBase':
        """Ensure title and prompt are not identical."""
        if self.title.lower().strip() == self.prompt.lower().strip():
            raise ValueError("Title and prompt cannot be identical")
        return self


class ControlCreate(ControlBase):
    """Schema for creating a new control."""

    @computed_field
    @property
    def is_question_format(self) -> bool:
        """Check if prompt is in question format."""
        return self.prompt.strip().endswith('?')


class ControlUpdate(BaseSchema):
    title: Annotated[str, StringConstraints(min_length=1, max_length=255)] | None = None
    description: OptionalNonEmptyStr = None
    prompt: NonEmptyStr | None = None
    is_active: bool | None = None

    @field_validator('prompt')
    @classmethod
    def validate_prompt_format(cls, v: str | None) -> str | None:
        """Ensure prompt is properly formatted when provided."""
        if v is not None:
            v = v.strip()
            if not v.endswith(('?', '.', '!')):
                v += '?'
        return v

    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> 'ControlUpdate':
        """Ensure at least one field is provided for update."""
        fields_provided = [
            self.title, self.description, self.prompt, self.is_active
        ]
        if all(field is None for field in fields_provided):
            raise ValueError("At least one field must be provided for update")
        return self


class ControlResponse(ControlBase):
    id: UUIDStr
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    @computed_field
    @property
    def status_display(self) -> str:
        """Human-readable status display."""
        return "Active" if self.is_active else "Inactive"


class ControlWithDocuments(ControlResponse):
    documents: list["DocumentResponse"] = Field(default_factory=list, description="Associated documents")

    @computed_field
    @property
    def document_count(self) -> int:
        """Number of associated documents."""
        return len(self.documents)


# Document Schemas with enhanced validation
class DocumentBase(BaseSchema):
    filename: FileName = Field(..., description="Unique filename for storage")
    original_filename: FileName = Field(..., description="Original uploaded filename")
    file_type: NonEmptyStr = Field(..., description="MIME type of the file")
    file_size: PositiveInt = Field(..., description="File size in bytes")

    @field_validator('file_type')
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """Validate MIME type format."""
        if '/' not in v:
            raise ValueError("Invalid MIME type format")
        return v.lower()

    @field_validator('file_size')
    @classmethod
    def validate_file_size_limit(cls, v: int) -> int:
        """Validate file size is within acceptable limits."""
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        if v > MAX_FILE_SIZE:
            raise ValueError(f"File size {v} exceeds maximum allowed size of {MAX_FILE_SIZE} bytes")
        return v

    @computed_field
    @property
    def file_size_mb(self) -> float:
        """File size in megabytes."""
        return round(self.file_size / (1024 * 1024), 2)


class DocumentCreate(DocumentBase):
    control_id: UUIDStr = Field(..., description="ID of the associated control")


class DocumentResponse(DocumentBase):
    id: UUIDStr
    control_id: UUIDStr
    file_url: HttpUrl | None = Field(None, description="Public file URL")
    signed_url: HttpUrl | None = Field(None, description="Temporary signed URL")
    reducto_file_id: str | None = Field(None, description="Reducto service file ID")
    extraction_status: ExtractionStatus
    created_at: datetime
    updated_at: datetime | None = None

    @computed_field
    @property
    def is_ready_for_processing(self) -> bool:
        """Check if document is ready for AI processing."""
        return ExtractionStatus.is_ready_for_ai_processing(self.extraction_status)

    @computed_field
    @property
    def file_extension(self) -> str:
        """Extract file extension from filename."""
        return self.original_filename.split('.')[-1].lower() if '.' in self.original_filename else ''


class DocumentWithContent(DocumentResponse):
    parsed_content: dict[str, Any] | None = Field(None, description="Parsed document content")

    @computed_field
    @property
    def has_content(self) -> bool:
        """Check if document has parsed content."""
        return self.parsed_content is not None and bool(self.parsed_content)


# AI Response Schemas with enhanced validation
class AIResponseBase(BaseSchema):
    response_text: str | None = Field(None, description="AI-generated response text")
    confidence_score: ConfidenceScore | None = Field(None, description="AI confidence score")
    citations: list[dict[str, Any]] | None = Field(None, description="Citation information")
    response_metadata: dict[str, Any] | None = Field(None, description="Additional response metadata")

    @field_validator('response_text')
    @classmethod
    def validate_response_text(cls, v: str | None) -> str | None:
        """Validate response text format."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator('citations')
    @classmethod
    def validate_citations_format(cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        """Validate citations have required fields."""
        if v is not None:
            for citation in v:
                if 'source' not in citation:
                    raise ValueError("Each citation must have a 'source' field")
        return v


class AIResponseCreate(AIResponseBase):
    control_id: UUIDStr = Field(..., description="ID of the associated control")
    document_id: UUIDStr = Field(..., description="ID of the associated document")


class AIResponseResponse(AIResponseBase):
    id: UUIDStr
    control_id: UUIDStr
    document_id: UUIDStr
    status: ProcessingStatus
    error_message: str | None = Field(None, description="Error message if processing failed")
    openai_model: str | None = Field(None, description="OpenAI model used")
    tokens_used: PositiveInt | None = Field(None, description="Number of tokens consumed")
    processing_time_ms: PositiveInt | None = Field(None, description="Processing time in milliseconds")
    created_at: datetime
    updated_at: datetime | None = None

    @computed_field
    @property
    def is_processing_complete(self) -> bool:
        """Check if AI processing is complete."""
        return ProcessingStatus.is_terminal_status(self.status)

    @computed_field
    @property
    def processing_time_seconds(self) -> float | None:
        """Processing time in seconds."""
        return self.processing_time_ms / 1000 if self.processing_time_ms else None


# File Upload Schemas
class FileUploadResponse(BaseSchema):
    id: UUIDStr
    filename: FileName
    file_size: PositiveInt
    file_type: NonEmptyStr
    upload_status: NonEmptyStr

    @computed_field
    @property
    def upload_successful(self) -> bool:
        """Check if upload was successful."""
        return self.upload_status.lower() in {'completed', 'success', 'uploaded'}


class BatchUploadResponse(BaseSchema):
    uploaded_files: list[FileUploadResponse] = Field(default_factory=list)
    failed_files: list[dict[str, str]] = Field(default_factory=list)

    @computed_field
    @property
    def success_count(self) -> int:
        """Number of successfully uploaded files."""
        return len(self.uploaded_files)

    @computed_field
    @property
    def failure_count(self) -> int:
        """Number of failed uploads."""
        return len(self.failed_files)

    @computed_field
    @property
    def total_attempted(self) -> int:
        """Total number of upload attempts."""
        return self.success_count + self.failure_count


# Tabular View Schemas
class CellResponse(BaseSchema):
    """Response for a single table cell (document-control combination)."""
    document_id: UUIDStr
    control_id: UUIDStr
    document_filename: FileName
    control_title: ControlTitle
    ai_response: AIResponseResponse | None = None
    status: ProcessingStatus

    @computed_field
    @property
    def has_response(self) -> bool:
        """Check if cell has an AI response."""
        return self.ai_response is not None

    @computed_field
    @property
    def is_actionable(self) -> bool:
        """Check if cell needs attention (failed or pending)."""
        return self.status in {ProcessingStatus.FAILED, ProcessingStatus.PENDING}


class TableRow(BaseSchema):
    """Response for a table row (document with all control responses)."""
    document: DocumentResponse
    cells: list[CellResponse] = Field(default_factory=list)

    @computed_field
    @property
    def completion_percentage(self) -> float:
        """Percentage of completed cells in this row."""
        if not self.cells:
            return 0.0
        completed = sum(1 for cell in self.cells if cell.status == ProcessingStatus.COMPLETED)
        return round((completed / len(self.cells)) * 100, 1)


class TableColumn(BaseSchema):
    """Response for a table column (control with all document responses)."""
    control: ControlResponse
    cells: list[CellResponse] = Field(default_factory=list)

    @computed_field
    @property
    def completion_percentage(self) -> float:
        """Percentage of completed cells in this column."""
        if not self.cells:
            return 0.0
        completed = sum(1 for cell in self.cells if cell.status == ProcessingStatus.COMPLETED)
        return round((completed / len(self.cells)) * 100, 1)


class TabularViewResponse(BaseSchema):
    """Complete tabular view response."""
    controls: list[ControlResponse] = Field(default_factory=list)
    documents: list[DocumentResponse] = Field(default_factory=list)
    rows: list[TableRow] = Field(default_factory=list)
    processing_count: Annotated[int, Field(ge=0)] = Field(0, description="Number of cells currently processing")

    @computed_field
    @property
    def total_cells(self) -> int:
        """Total number of cells in the table."""
        return len(self.controls) * len(self.documents)

    @computed_field
    @property
    def overall_completion_percentage(self) -> float:
        """Overall completion percentage for the entire table."""
        if self.total_cells == 0:
            return 100.0
        total_completed = sum(row.completion_percentage * len(row.cells) / 100 for row in self.rows)
        return round((total_completed / self.total_cells) * 100, 1) if self.total_cells > 0 else 0.0


# Task Queue Schemas
class TaskCreate(BaseSchema):
    task_type: NonEmptyStr = Field(..., description="Type of task to be processed")
    task_data: dict[str, Any] = Field(..., description="Task-specific data")
    priority: Annotated[int, Field(ge=0, le=10)] = Field(0, description="Task priority (0-10)")

    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        """Validate task type format."""
        valid_types = {'document_parse', 'ai_process', 'file_upload', 'regenerate'}
        if v not in valid_types:
            raise ValueError(f"Task type must be one of: {', '.join(valid_types)}")
        return v


class TaskResponse(BaseSchema):
    id: UUIDStr
    task_type: NonEmptyStr
    status: ProcessingStatus
    priority: Annotated[int, Field(ge=0, le=10)]
    retry_count: Annotated[int, Field(ge=0)]
    max_retries: Annotated[int, Field(ge=0)]
    error_message: str | None = None
    result_data: dict[str, Any] | None = None
    created_at: datetime

    @computed_field
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.status == ProcessingStatus.FAILED


# Regeneration Schemas
class RegenerateRequest(BaseSchema):
    control_id: UUIDStr | None = Field(None, description="Regenerate all responses for this control")
    document_id: UUIDStr | None = Field(None, description="Regenerate all responses for this document")
    ai_response_id: UUIDStr | None = Field(None, description="Regenerate this specific response")

    @model_validator(mode='after')
    def validate_exactly_one_id(self) -> 'RegenerateRequest':
        """Ensure exactly one ID is provided."""
        ids_provided = [self.control_id, self.document_id, self.ai_response_id]
        non_none_ids = [id for id in ids_provided if id is not None]

        if len(non_none_ids) != 1:
            raise ValueError("Exactly one of control_id, document_id, or ai_response_id must be provided")
        return self

    @computed_field
    @property
    def regeneration_scope(self) -> str:
        """Describe the scope of regeneration."""
        if self.control_id:
            return "control"
        elif self.document_id:
            return "document"
        else:
            return "single_response"


# Response Schemas
class DefaultResponse(BaseSchema):
    status: bool = Field(..., description="Operation success status")
    message: NonEmptyStr = Field(..., description="Human-readable message")
    details: dict[str, Any] | None = Field(None, description="Additional details")

    @computed_field
    @property
    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.status


class ErrorResponse(BaseSchema):
    error: NonEmptyStr = Field(..., description="Error type/code")
    detail: str | None = Field(None, description="Detailed error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

    @field_validator('error')
    @classmethod
    def validate_error_format(cls, v: str) -> str:
        """Ensure error follows standard format."""
        return v.upper().replace(' ', '_')


# Health Check Schema
class HealthCheckResponse(BaseSchema):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.now)
    checks: dict[str, bool] = Field(default_factory=dict, description="Individual service checks")

    @computed_field
    @property
    def is_healthy(self) -> bool:
        """Check if all services are healthy."""
        return all(self.checks.values()) if self.checks else True


# Storage and Bucket Models for Supabase integration
class BucketInfoResponse(BaseSchema):
    """Response model for bucket information"""
    id: str = Field(..., description="Unique bucket identifier")
    name: str = Field(..., description="Bucket name")
    public: bool = Field(..., description="Whether bucket is public")
    created_at: datetime = Field(..., description="When the bucket was created")
    file_size_limit: OptionalPositiveInt = Field(None, description="Maximum file size in bytes")
    allowed_mime_types: list[str] | None = Field(None, description="Allowed MIME types")


class PresignedUrlResponse(BaseSchema):
    """Response model for presigned URLs"""
    upload_url: HttpUrl = Field(..., description="Presigned upload URL")
    file_path: NonEmptyStr = Field(..., description="Path where file will be stored")
    expires_at: datetime = Field(..., description="When the URL expires")
    bucket_name: NonEmptyStr = Field(..., description="Target bucket name")
    max_file_size: PositiveInt = Field(..., description="Maximum allowed file size in bytes")


class FileMetadataResponse(BaseSchema):
    """Response model for file metadata"""
    name: FileName = Field(..., description="Original file name")
    size: NonNegativeInt = Field(..., description="File size in bytes")
    content_type: NonEmptyStr = Field(..., description="MIME type of the file")
    path: NonEmptyStr = Field(..., description="Storage path of the file")
    bucket: NonEmptyStr = Field(..., description="Bucket containing the file")
    uploaded_at: datetime = Field(..., description="When the file was uploaded")
    uploaded_by: OptionalNonEmptyStr = Field(None, description="User who uploaded the file")

    @computed_field
    @property
    def size_readable(self) -> str:
        """Human-readable file size"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.1f} GB"


class StorageHealthResponse(BaseSchema):
    """Response model for storage health check"""
    status: str = Field(..., description="Health status")
    connected: bool = Field(..., description="Whether connection is successful")
    buckets_count: NonNegativeInt = Field(..., description="Number of available buckets")
    buckets: list[str] = Field(default_factory=list, description="List of bucket names")
    error: OptionalNonEmptyStr = Field(None, description="Error message if any")


class BucketCreateRequest(BaseSchema):
    """Request model for creating a bucket"""
    bucket_name: Annotated[str, StringConstraints(
        min_length=3,
        max_length=63,
        pattern=r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$'
    )] = Field(..., description="Bucket name (3-63 chars, lowercase, alphanumeric + hyphens)")
    public: bool = Field(False, description="Whether bucket should be public")
    file_size_limit: OptionalPositiveInt = Field(None, description="Maximum file size in bytes")
    allowed_mime_types: list[str] | None = Field(None, description="Allowed MIME types")

    @field_validator('bucket_name')
    @classmethod
    def validate_bucket_name(cls, v: str) -> str:
        """Validate bucket name follows AWS S3 naming conventions"""
        if not v:
            raise ValueError("Bucket name cannot be empty")

        # Additional validation beyond the regex
        if v.startswith('-') or v.endswith('-'):
            raise ValueError("Bucket name cannot start or end with hyphen")

        if '--' in v:
            raise ValueError("Bucket name cannot contain consecutive hyphens")

        return v.lower()


class UploadUrlRequest(BaseSchema):
    """Request model for generating upload URLs"""
    file_name: FileName = Field(..., description="Name of the file to upload")
    content_type: NonEmptyStr = Field(..., description="MIME type of the file")
    bucket_name: NonEmptyStr = Field("tally-documents", description="Target bucket name")
    user_id: OptionalNonEmptyStr = Field(None, description="Optional user ID for file organization")

    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type is allowed"""
        # This would typically come from config, but we'll define allowed types here
        allowed_types = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain",
            "text/csv",
            "image/jpeg",
            "image/png",
            "image/webp"
        }

        if v not in allowed_types:
            raise ValueError(f"Content type '{v}' is not allowed. Allowed types: {', '.join(allowed_types)}")

        return v


class BucketCreateResponse(BaseSchema):
    """Response model for bucket creation"""
    success: bool = Field(..., description="Whether bucket was created successfully")
    bucket_name: NonEmptyStr = Field(..., description="Name of the created bucket")
    message: NonEmptyStr = Field(..., description="Success or error message")
    bucket_info: dict[str, Any] | None = Field(None, description="Additional bucket information")
    error_type: OptionalNonEmptyStr = Field(None, description="Type of error if creation failed")


# Forward reference resolution
ControlWithDocuments.model_rebuild()

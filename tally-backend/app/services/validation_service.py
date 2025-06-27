"""
Advanced validation service using Pydantic v2 features.

This service provides comprehensive validation patterns including:
- Custom validators
- Conditional validation
- Cross-field validation
- Data sanitization
- Type coercion with strict rules
"""

import re
from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel, ValidationError

from app.schemas import (
    AIResponseCreate,
    ControlCreate,
    DocumentCreate,
    ErrorResponse,
    ProcessingStatus,
)

T = TypeVar('T', bound=BaseModel)


class ValidationService:
    """Advanced validation service using Pydantic v2 features."""

    @staticmethod
    def validate_model_strict(model_class: type[T], data: dict[str, Any]) -> T:
        """
        Validate data against a Pydantic model with strict mode enabled.
        
        Args:
            model_class: The Pydantic model class to validate against
            data: The data dictionary to validate
            
        Returns:
            Validated model instance
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Create a temporary model class with strict validation
            class StrictModel(model_class):
                model_config = model_class.model_config.copy()
                model_config.update({"strict": True})

            return StrictModel.model_validate(data)
        except ValidationError as e:
            raise ValidationError.from_exception_data(
                title="Strict Validation Failed",
                line_errors=e.errors()
            )

    @staticmethod
    def sanitize_and_validate(
        model_class: type[T],
        data: dict[str, Any],
        strict_fields: list[str] | None = None
    ) -> T:
        """
        Sanitize input data and validate with selective strict mode.
        
        Args:
            model_class: The Pydantic model class
            data: Input data to sanitize and validate
            strict_fields: List of field names to apply strict validation to
            
        Returns:
            Validated and sanitized model instance
        """
        # Data sanitization
        sanitized_data = ValidationService._sanitize_input_data(data)

        # Apply strict validation to specific fields if specified
        if strict_fields:
            for field_name in strict_fields:
                if field_name in sanitized_data:
                    field_value = sanitized_data[field_name]
                    # Apply additional strict validation based on field type
                    sanitized_data[field_name] = ValidationService._apply_strict_field_validation(
                        field_name, field_value, model_class
                    )

        return model_class.model_validate(sanitized_data)

    @staticmethod
    def _sanitize_input_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize input data by removing potentially harmful content.
        
        Args:
            data: Raw input data
            
        Returns:
            Sanitized data dictionary
        """
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Remove potential XSS patterns
                value = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', value, flags=re.IGNORECASE)
                # Remove SQL injection patterns
                value = re.sub(r'(;|--|\/\*|\*\/|union|select|insert|update|delete|drop|create|alter)', '', value, flags=re.IGNORECASE)
                # Trim whitespace
                value = value.strip()

            elif isinstance(value, dict):
                value = ValidationService._sanitize_input_data(value)
            elif isinstance(value, list):
                value = [
                    ValidationService._sanitize_input_data(item) if isinstance(item, dict)
                    else item for item in value
                ]

            sanitized[key] = value

        return sanitized

    @staticmethod
    def _apply_strict_field_validation(field_name: str, value: Any, model_class: type[BaseModel]) -> Any:
        """
        Apply strict validation rules to specific fields.
        
        Args:
            field_name: Name of the field
            value: Field value
            model_class: The model class containing the field
            
        Returns:
            Validated field value
        """
        # Get field info from the model
        field_info = model_class.model_fields.get(field_name)
        if not field_info:
            return value

        # Apply strict validation based on field type
        if field_name.endswith('_id') and isinstance(value, str):
            # Validate UUID format for ID fields
            try:
                UUID(value)
                return value
            except ValueError:
                raise ValueError(f"Field '{field_name}' must be a valid UUID")

        if field_name in ['email'] and isinstance(value, str):
            # Strict email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValueError(f"Field '{field_name}' must be a valid email address")

        if field_name in ['filename', 'original_filename'] and isinstance(value, str):
            # Validate filename safety
            if re.search(r'[<>:"/\\|?*\x00-\x1f]', value):
                raise ValueError(f"Field '{field_name}' contains invalid characters")

        return value

    @staticmethod
    def validate_business_rules(model: BaseModel) -> list[str]:
        """
        Validate business-specific rules that go beyond basic field validation.
        
        Args:
            model: The validated Pydantic model instance
            
        Returns:
            List of business rule validation errors (empty if all valid)
        """
        errors = []

        # Control-specific business rules
        if isinstance(model, ControlCreate):
            if len(model.prompt.split()) < 3:
                errors.append("Control prompt must contain at least 3 words")

            if not any(char in model.prompt for char in ['?', 'what', 'how', 'when', 'where', 'why']):
                errors.append("Control prompt should be phrased as a question")

        # Document-specific business rules
        elif isinstance(model, DocumentCreate):
            allowed_types = [
                'application/pdf', 'text/plain', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            if model.file_type not in allowed_types:
                errors.append(f"File type '{model.file_type}' is not supported")

            if model.file_size > 50 * 1024 * 1024:  # 50MB limit
                errors.append("File size exceeds maximum allowed limit of 50MB")

        # AI Response business rules
        elif isinstance(model, AIResponseCreate):
            # Validate that control_id and document_id are different
            if model.control_id == model.document_id:
                errors.append("Control ID and Document ID cannot be the same")

        return errors

    @staticmethod
    def create_validation_error_response(
        validation_error: ValidationError,
        request_id: str | None = None
    ) -> ErrorResponse:
        """
        Create a standardized error response from Pydantic validation errors.
        
        Args:
            validation_error: The Pydantic validation error
            request_id: Optional request ID for tracking
            
        Returns:
            Standardized error response
        """
        error_details = {
            "validation_errors": [
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                    "input": error.get("input")
                }
                for error in validation_error.errors()
            ]
        }

        if request_id:
            error_details["request_id"] = request_id

        return ErrorResponse(
            error="VALIDATION_ERROR",
            detail=f"Validation failed with {len(validation_error.errors())} error(s)",
            timestamp=datetime.now()
        )

    @staticmethod
    def validate_with_context(
        model_class: type[T],
        data: dict[str, Any],
        context: dict[str, Any]
    ) -> T:
        """
        Validate a model with additional context for cross-validation.
        
        Args:
            model_class: The Pydantic model class
            data: Data to validate
            context: Additional context for validation
            
        Returns:
            Validated model instance
        """
        return model_class.model_validate(data, context=context)

    @staticmethod
    def batch_validate(
        model_class: type[T],
        data_list: list[dict[str, Any]],
        fail_fast: bool = False
    ) -> tuple[list[T], list[tuple[int, ValidationError]]]:
        """
        Validate multiple data items in batch.
        
        Args:
            model_class: The Pydantic model class
            data_list: List of data dictionaries to validate
            fail_fast: Whether to stop on first validation error
            
        Returns:
            Tuple of (valid_models, errors) where errors is list of (index, error) tuples
        """
        valid_models = []
        errors = []

        for i, data in enumerate(data_list):
            try:
                model = model_class.model_validate(data)
                valid_models.append(model)
            except ValidationError as e:
                errors.append((i, e))
                if fail_fast:
                    break

        return valid_models, errors


class AdvancedFieldValidators:
    """Collection of reusable field validators for common patterns."""

    @staticmethod
    def validate_uuid_string(value: str) -> str:
        """Validate that a string is a valid UUID."""
        try:
            UUID(value)
            return value
        except ValueError:
            raise ValueError("Must be a valid UUID string")

    @staticmethod
    def validate_positive_integer(value: int) -> int:
        """Validate that an integer is positive."""
        if value <= 0:
            raise ValueError("Must be a positive integer")
        return value

    @staticmethod
    def validate_filename_safe(value: str) -> str:
        """Validate that a filename is safe for filesystem storage."""
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', value):
            raise ValueError("Filename contains invalid characters")
        if len(value) > 255:
            raise ValueError("Filename too long (max 255 characters)")
        return value

    @staticmethod
    def validate_mime_type(value: str) -> str:
        """Validate MIME type format."""
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^]*\/[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^]*$', value):
            raise ValueError("Invalid MIME type format")
        return value.lower()

    @staticmethod
    def validate_processing_status_transition(
        current_status: ProcessingStatus,
        new_status: ProcessingStatus
    ) -> ProcessingStatus:
        """Validate status transitions are logical."""
        valid_transitions = {
            ProcessingStatus.PENDING: [ProcessingStatus.PROCESSING, ProcessingStatus.FAILED],
            ProcessingStatus.PROCESSING: [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.REGENERATING],
            ProcessingStatus.COMPLETED: [ProcessingStatus.REGENERATING],
            ProcessingStatus.FAILED: [ProcessingStatus.PROCESSING, ProcessingStatus.REGENERATING],
            ProcessingStatus.REGENERATING: [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise ValueError(f"Invalid status transition from {current_status} to {new_status}")

        return new_status

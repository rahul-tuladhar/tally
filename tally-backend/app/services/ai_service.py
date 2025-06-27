import asyncio
import time
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.schemas import AIResponseResponse, ProcessingStatus


class AIService:
    """Service for handling AI operations using OpenAI."""

    def __init__(self):
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY
        )

    async def process_document(
        self,
        document_content: str,
        control_prompt: str,
        force_regenerate: bool = False
    ) -> AIResponseResponse:
        """Process a document with a control prompt to generate AI response."""
        try:
            # Generate AI response
            start_time = time.time()
            response_data = await self._generate_ai_response(document_content, control_prompt)
            processing_time = int((time.time() - start_time) * 1000)

            return AIResponseResponse(
                response_text=response_data["response_text"],
                confidence_score=response_data.get("confidence_score"),
                citations=response_data.get("citations", []),
                metadata=response_data.get("metadata", {}),
                tokens_used=response_data.get("tokens_used"),
                processing_time_ms=processing_time,
                status=ProcessingStatus.COMPLETED,
                error_message=None
            )

        except Exception as e:
            return AIResponseResponse(
                response_text="",
                confidence_score=0.0,
                citations=[],
                metadata={},
                tokens_used=0,
                processing_time_ms=0,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )

    async def process_multiple_documents(
        self,
        documents: list[tuple[str, str]],  # List of (document_content, control_prompt) pairs
        force_regenerate: bool = False
    ) -> list[AIResponseResponse]:
        """Process multiple documents with their respective control prompts."""
        tasks = []
        for doc_content, control_prompt in documents:
            task = self.process_document(doc_content, control_prompt, force_regenerate)
            tasks.append(task)

        # Process in parallel with controlled concurrency
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests

        async def process_with_semaphore(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(
            *[process_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        # Filter out exceptions and return successful results
        successful_results = []
        for result in results:
            if isinstance(result, AIResponseResponse):
                successful_results.append(result)
            elif isinstance(result, Exception):
                # Log error but continue with other results
                print(f"AI processing error: {result}")

        return successful_results

    async def _generate_ai_response(
        self,
        document_content: str,
        control_prompt: str
    ) -> dict[str, Any]:
        """Generate AI response using OpenAI."""
        try:
            # Create prompts
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(control_prompt, document_content)

            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
            )

            # Extract response data
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # Calculate confidence score (simplified heuristic)
            confidence_score = self._calculate_confidence_score(response_text)

            return {
                "response_text": response_text,
                "confidence_score": confidence_score,
                "citations": [],  # Simplified for now
                "tokens_used": tokens_used,
                "metadata": {
                    "model": settings.OPENAI_MODEL,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "finish_reason": response.choices[0].finish_reason
                }
            }

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def _create_system_prompt(self) -> str:
        """Create system prompt for AI processing."""
        return """You are an AI assistant specialized in analyzing documents for compliance and control requirements.
        Your task is to evaluate the provided document content against the specified control criteria.
        Provide clear, concise responses with specific references to relevant sections of the document.
        If you cannot find relevant information, clearly state that the document does not address the control requirements."""

    def _create_user_prompt(self, control_prompt: str, document_content: str) -> str:
        """Create user prompt for AI processing."""
        return f"""Please analyze the following document content for compliance with the specified control requirements:

Control Requirements:
{control_prompt}

Document Content:
{document_content}

Please provide:
1. An assessment of whether the document satisfies the control requirements
2. Specific references to relevant sections of the document
3. Any gaps or areas where the document does not fully address the requirements"""

    def _calculate_confidence_score(self, response_text: str) -> float:
        """Calculate a confidence score based on the response text."""
        # Simplified confidence scoring
        confidence_indicators = [
            "clearly states",
            "explicitly mentions",
            "directly addresses",
            "specifically outlines",
            "demonstrates",
        ]
        uncertainty_indicators = [
            "unclear",
            "may",
            "might",
            "possibly",
            "cannot determine",
            "insufficient information",
        ]

        confidence_count = sum(1 for indicator in confidence_indicators if indicator.lower() in response_text.lower())
        uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator.lower() in response_text.lower())

        # Calculate base score
        total_indicators = len(confidence_indicators) + len(uncertainty_indicators)
        base_score = (confidence_count - uncertainty_count) / total_indicators

        # Normalize to 0-1 range
        normalized_score = (base_score + 1) / 2

        return round(max(0.1, min(0.9, normalized_score)), 2)  # Clamp between 0.1 and 0.9

    async def close(self) -> None:
        """Cleanup resources."""
        await self.openai_client.close()

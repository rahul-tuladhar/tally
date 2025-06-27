
from fastapi import APIRouter, HTTPException

from app.schemas import AIResponseRequest, AIResponseResponse
from app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()

@router.post("/analyze", response_model=AIResponseResponse)
async def analyze_document(request: AIResponseRequest) -> AIResponseResponse:
    """Analyze a document with AI."""
    try:
        return await ai_service.process_document(
            document_content=request.document_content,
            control_prompt=request.control_prompt,
            force_regenerate=request.force_regenerate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/batch", response_model=list[AIResponseResponse])
async def analyze_documents(requests: list[AIResponseRequest]) -> list[AIResponseResponse]:
    """Analyze multiple documents with AI in parallel."""
    try:
        documents = [(req.document_content, req.control_prompt) for req in requests]
        return await ai_service.process_multiple_documents(
            documents=documents,
            force_regenerate=any(req.force_regenerate for req in requests)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

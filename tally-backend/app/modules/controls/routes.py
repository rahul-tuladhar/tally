
from fastapi import APIRouter, HTTPException

from app.modules.controls.service import ControlService
from app.schemas import ControlResponse, CreateControlRequest, UpdateControlRequest

router = APIRouter()
control_service = ControlService()

@router.post("/", response_model=ControlResponse)
async def create_control(request: CreateControlRequest) -> ControlResponse:
    """Create a new control."""
    return await control_service.create_control(request)

@router.get("/{control_id}", response_model=ControlResponse)
async def get_control(control_id: str) -> ControlResponse:
    """Get control by ID."""
    control = await control_service.get_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control

@router.get("/", response_model=list[ControlResponse])
async def list_controls() -> list[ControlResponse]:
    """List all controls."""
    return await control_service.list_controls()

@router.put("/{control_id}", response_model=ControlResponse)
async def update_control(control_id: str, request: UpdateControlRequest) -> ControlResponse:
    """Update a control."""
    control = await control_service.update_control(control_id, request)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control

@router.delete("/{control_id}")
async def delete_control(control_id: str) -> dict:
    """Delete a control."""
    success = await control_service.delete_control(control_id)
    if not success:
        raise HTTPException(status_code=404, detail="Control not found")
    return {"message": "Control deleted successfully"}

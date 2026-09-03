
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.database import get_db
from apps.api.app.schemas.supervisor import SupervisorCreate, SupervisorResponse
from apps.api.app.services.supervisors import SupervisorService

router = APIRouter(prefix="/supervisors", tags=["Supervisors"])


@router.post("", response_model=SupervisorResponse, status_code=status.HTTP_201_CREATED)
async def create_supervisor(payload: SupervisorCreate, db: AsyncSession = Depends(get_db)):
    """Create a new Supervisor template configuration."""
    try:
        return await SupervisorService.create_supervisor(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[SupervisorResponse])
async def list_supervisors(db: AsyncSession = Depends(get_db)):
    """List all configured Supervisor templates."""
    return await SupervisorService.get_all_supervisors(db)


@router.get("/{supervisor_id}", response_model=SupervisorResponse)
async def get_supervisor(supervisor_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific Supervisor template configuration by ID."""
    sup = await SupervisorService.get_supervisor_by_id(db, supervisor_id)
    if not sup:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    return sup


@router.delete("/{supervisor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supervisor(supervisor_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a Supervisor template configuration."""
    deleted = await SupervisorService.delete_supervisor(db, supervisor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

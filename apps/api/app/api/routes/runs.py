
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.database import get_db
from apps.api.app.schemas.event import EventCreate, EventResponse
from apps.api.app.schemas.instruction import InstructionCreate, InstructionResponse
from apps.api.app.schemas.run import RunCreate, RunDetailResponse, RunResponse
from apps.api.app.services.runs import RunService

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(payload: RunCreate, db: AsyncSession = Depends(get_db)):
    """Start an Order Supervisor workflow run for an order."""
    try:
        return await RunService.create_run(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[RunResponse])
async def list_runs(db: AsyncSession = Depends(get_db)):
    """List all active and completed runs."""
    return await RunService.get_all_runs(db)


@router.get("/{run_id}", response_model=RunDetailResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Get full details of a run, including its event timeline and agent activities."""
    run = await RunService.get_run_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def inject_event(run_id: str, payload: EventCreate, db: AsyncSession = Depends(get_db)):
    """Inject an event/signal into a running Order Supervisor workflow."""
    try:
        return await RunService.add_event(db, run_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{run_id}/instructions", response_model=InstructionResponse, status_code=status.HTTP_201_CREATED)
async def inject_instruction(run_id: str, payload: InstructionCreate, db: AsyncSession = Depends(get_db)):
    """Inject live runtime guidance or steering instructions to an active order workflow."""
    try:
        return await RunService.add_instruction(db, run_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{run_id}/interrupt", response_model=RunResponse)
async def interrupt_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Pause/interrupt a running workflow."""
    try:
        return await RunService.pause_run(db, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{run_id}/resume", response_model=RunResponse)
async def resume_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Resume a paused workflow."""
    try:
        return await RunService.resume_run(db, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{run_id}/terminate", response_model=RunResponse)
async def terminate_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Terminate an order workflow run."""
    try:
        return await RunService.terminate_run(db, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

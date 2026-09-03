import uuid

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from apps.api.app.models.supervisor import SupervisorModel
from apps.api.app.schemas.supervisor import SupervisorCreate


class SupervisorService:
    @staticmethod
    async def create_supervisor(db: AsyncSession, data: SupervisorCreate) -> SupervisorModel:
        clean_name = data.name.strip()
        # Prevent creating duplicates with the same profile name
        existing_result = await db.execute(
            select(SupervisorModel).where(func.lower(SupervisorModel.name) == func.lower(clean_name))
        )
        if existing_result.scalar_one_or_none():
            raise ValueError(f"A supervisor profile named '{clean_name}' already exists. Please choose a unique name.")

        supervisor_id = f"sup_{uuid.uuid4().hex[:8]}"
        supervisor = SupervisorModel(
            id=supervisor_id,
            name=clean_name,
            description=data.description,
            base_instruction=data.base_instruction,
            available_tools=data.available_tools,
            default_wake_delay_seconds=data.default_wake_delay_seconds,
            wake_sensitivity=data.wake_sensitivity,
            model_name=data.model_name,
            is_active=data.is_active,
        )
        db.add(supervisor)
        await db.commit()
        await db.refresh(supervisor)
        return supervisor

    @staticmethod
    async def get_all_supervisors(db: AsyncSession) -> list[SupervisorModel]:
        result = await db.execute(select(SupervisorModel).order_by(SupervisorModel.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_supervisor_by_id(db: AsyncSession, supervisor_id: str) -> SupervisorModel | None:
        result = await db.execute(select(SupervisorModel).where(SupervisorModel.id == supervisor_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_supervisor(db: AsyncSession, supervisor_id: str) -> bool:
        supervisor = await SupervisorService.get_supervisor_by_id(db, supervisor_id)
        if not supervisor:
            return False
        await db.delete(supervisor)
        await db.commit()
        return True

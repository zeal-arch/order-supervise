from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from apps.api.app.db.database import Base


class SupervisorModel(Base):
    __tablename__ = "supervisors"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    base_instruction = Column(Text, nullable=False)
    available_tools = Column(JSON, default=list, nullable=False)
    default_wake_delay_seconds = Column(Integer, default=3600, nullable=False)
    wake_sensitivity = Column(String(32), default="balanced", nullable=False)
    model_name = Column(String(64), default="gpt-4o-mini", nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

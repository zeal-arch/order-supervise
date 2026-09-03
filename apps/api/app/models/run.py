from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from apps.api.app.db.database import Base


class RunModel(Base):
    __tablename__ = "runs"

    id = Column(String(64), primary_key=True, index=True)
    order_id = Column(String(64), nullable=False, index=True)
    supervisor_id = Column(String(64), ForeignKey("supervisors.id"), nullable=True)
    workflow_id = Column(String(128), unique=True, nullable=False, index=True)
    run_id = Column(String(128), nullable=True)
    status = Column(String(32), default="INITIALIZING", nullable=False, index=True)

    order_context = Column(JSON, default=dict, nullable=False)
    current_memory = Column(JSON, default=dict, nullable=False)
    additional_instructions = Column(JSON, default=list, nullable=False)

    next_wake_at = Column(DateTime(timezone=True), nullable=True)
    last_wake_reason = Column(String(64), nullable=True)

    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    final_output = Column(JSON, nullable=True)

    # Relationships
    events = relationship("EventModel", back_populates="run", cascade="all, delete-orphan")
    activities = relationship("ActivityModel", back_populates="run", cascade="all, delete-orphan")

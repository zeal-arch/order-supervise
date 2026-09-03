from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from apps.api.app.db.database import Base


class EventModel(Base):
    __tablename__ = "events"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    source = Column(String(64), default="simulator", nullable=False)
    requires_wake = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    run = relationship("RunModel", back_populates="events")

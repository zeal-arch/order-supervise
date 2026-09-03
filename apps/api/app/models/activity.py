from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from apps.api.app.db.database import Base


class ActivityModel(Base):
    __tablename__ = "activities"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type = Column(String(64), nullable=False)
    reasoning = Column(Text, nullable=True)
    payload = Column(JSON, default=dict, nullable=False)
    result = Column(JSON, default=dict, nullable=False)
    status = Column(String(32), default="SUCCESS", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    run = relationship("RunModel", back_populates="activities")

from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from datetime import datetime, timezone
from app.database import Base


class ComplianceEvent(Base):
    __tablename__ = "compliance_events"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    zone = Column(String)
    person_track_id = Column(Integer)
    helmet_detected = Column(Boolean)
    vest_detected = Column(Boolean)
    is_compliant = Column(Boolean)
    missing_items = Column(String)  # comma-separated
    frame_number = Column(Integer)
    evidence_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String, primary_key=True)
    source_filename = Column(String)
    zone = Column(String)
    total_people = Column(Integer, default=0)
    compliant_count = Column(Integer, default=0)
    non_compliant_count = Column(Integer, default=0)
    status = Column(String, default="processing")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

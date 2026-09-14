from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ComplianceEventOut(BaseModel):
    id: int
    session_id: str
    zone: str
    person_track_id: int
    helmet_detected: bool
    vest_detected: bool
    is_compliant: bool
    missing_items: str
    frame_number: int
    evidence_path: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class SessionOut(BaseModel):
    id: str
    source_filename: str
    zone: str
    total_people: int
    compliant_count: int
    non_compliant_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_people_checked: int
    compliance_rate_pct: float
    non_compliant_events: int
    total_sessions: int

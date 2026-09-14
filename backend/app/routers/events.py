import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import ComplianceEvent, AnalysisSession
from app.schemas import ComplianceEventOut, DashboardSummary

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events", response_model=List[ComplianceEventOut])
def list_events(limit: int = 200, db: Session = Depends(get_db)):
    return db.query(ComplianceEvent).order_by(ComplianceEvent.timestamp.desc()).limit(limit).all()


@router.get("/events/export")
def export_events(db: Session = Depends(get_db)):
    events = db.query(ComplianceEvent).order_by(ComplianceEvent.timestamp.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "session_id", "zone", "person_track_id", "helmet", "vest", "compliant", "missing", "timestamp"])
    for e in events:
        writer.writerow([e.id, e.session_id, e.zone, e.person_track_id, e.helmet_detected, e.vest_detected, e.is_compliant, e.missing_items, e.timestamp])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ppe_events.csv"},
    )


@router.get("/dashboard/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)):
    total = db.query(func.count(ComplianceEvent.id)).scalar() or 0
    compliant = db.query(func.count(ComplianceEvent.id)).filter(ComplianceEvent.is_compliant == True).scalar() or 0  # noqa: E712
    non_compliant = total - compliant
    total_sessions = db.query(func.count(AnalysisSession.id)).scalar() or 0
    rate = round((compliant / total * 100), 1) if total else 0.0
    return DashboardSummary(
        total_people_checked=total, compliance_rate_pct=rate,
        non_compliant_events=non_compliant, total_sessions=total_sessions,
    )

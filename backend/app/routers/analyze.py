import os
import uuid
import cv2
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisSession, ComplianceEvent
from app.schemas import SessionOut
from app.config import settings
from app.detection import process_source, process_video

router = APIRouter(prefix="/api/analyze", tags=["analyze"])

DEMO_VIDEO = os.path.join(os.path.dirname(__file__), "..", "..", "demo", "worker-zone-demo.mp4")


def _persist(db: Session, session_id: str, filename: str, zone: str, result: dict):
    session = AnalysisSession(
        id=session_id, source_filename=filename, zone=zone,
        total_people=result["total_people"], compliant_count=result["compliant_count"],
        non_compliant_count=result["non_compliant_count"], status="completed",
    )
    db.add(session)
    for e in result["events"]:
        db.add(ComplianceEvent(
            session_id=session_id, zone=zone,
            person_track_id=e["person_track_id"], helmet_detected=e["helmet_detected"],
            vest_detected=e["vest_detected"], is_compliant=e["is_compliant"],
            missing_items=e["missing_items"], frame_number=e.get("frame_number", 0),
        ))
    db.commit()
    db.refresh(session)
    return session


@router.post("/demo", response_model=SessionOut)
def analyze_demo(zone: str = Form(default="construction"), db: Session = Depends(get_db)):
    if not os.path.exists(DEMO_VIDEO):
        raise HTTPException(status_code=404, detail="Demo video not found on server")
    session_id = uuid.uuid4().hex[:12]
    result = process_video(DEMO_VIDEO, zone, settings.zone_rules)
    return _persist(db, session_id, "worker-zone-demo.mp4", zone, result)


@router.post("/image", response_model=SessionOut)
async def analyze_image(
    file: UploadFile = File(...),
    zone: str = Form(default="construction"),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    img_array = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    session_id = uuid.uuid4().hex[:12]
    result = process_source(frame, zone, settings.zone_rules)
    return _persist(db, session_id, file.filename, zone, result)

import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, HandwritingProfile, EnrollmentSheet, SheetStatus
from app.schemas import SheetUploadOut, SheetStatusOut
from app.config import settings
from app.services.enrollment_pipeline import process_sheet  # see services/enrollment_pipeline.py

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


def _get_profile_or_404(profile_id: str, user: User, db: Session) -> HandwritingProfile:
    profile = (
        db.query(HandwritingProfile)
        .filter(HandwritingProfile.id == profile_id, HandwritingProfile.user_id == user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Handwriting profile not found.")
    return profile


@router.post("/{profile_id}/sheets", response_model=SheetUploadOut)
def upload_sheet(
    profile_id: str,
    sheet_index: int = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = _get_profile_or_404(profile_id, user, db)
    if not (0 <= sheet_index < settings.required_sheets):
        raise HTTPException(status_code=400, detail=f"sheet_index must be between 0 and {settings.required_sheets - 1}.")

    raw_key = f"users/{user.id}/profiles/{profile.id}/sheets/{sheet_index}/{uuid.uuid4()}.jpg"
    # storage.upload(raw_key, file.file)  -- wire up your S3/MinIO client here

    sheet = EnrollmentSheet(
        profile_id=profile.id,
        sheet_index=sheet_index,
        raw_image_key=raw_key,
        status=SheetStatus.uploaded,
    )
    db.add(sheet)
    db.commit()
    db.refresh(sheet)

    # Segmentation/alignment/vectorization happens off the request thread so
    # the upload response is fast; the frontend polls sheet status after.
    background_tasks.add_task(process_sheet, sheet.id)

    return SheetUploadOut(sheet_id=sheet.id, sheet_index=sheet.sheet_index, status=sheet.status.value)


@router.get("/{profile_id}/sheets", response_model=list[SheetStatusOut])
def list_sheets(profile_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = _get_profile_or_404(profile_id, user, db)
    sheets = db.query(EnrollmentSheet).filter(EnrollmentSheet.profile_id == profile.id).all()
    return [
        SheetStatusOut(sheet_id=s.id, sheet_index=s.sheet_index, status=s.status.value, error_message=s.error_message)
        for s in sheets
    ]

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, HandwritingProfile, GlyphVariant
from app.schemas import GlyphOut, GlyphReviewUpdate

router = APIRouter(prefix="/profiles", tags=["glyphs"])


@router.get("/{profile_id}/glyphs", response_model=list[GlyphOut])
def list_glyphs(
    profile_id: str,
    only_needs_review: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = (
        db.query(HandwritingProfile)
        .filter(HandwritingProfile.id == profile_id, HandwritingProfile.user_id == user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Handwriting profile not found.")

    query = db.query(GlyphVariant).filter(GlyphVariant.profile_id == profile.id)
    if only_needs_review:
        query = query.filter(GlyphVariant.needs_review.is_(True))
    return query.all()


@router.patch("/glyphs/{glyph_id}", response_model=GlyphOut)
def review_glyph(
    glyph_id: str,
    body: GlyphReviewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    glyph = (
        db.query(GlyphVariant)
        .join(HandwritingProfile, GlyphVariant.profile_id == HandwritingProfile.id)
        .filter(GlyphVariant.id == glyph_id, HandwritingProfile.user_id == user.id)
        .first()
    )
    if not glyph:
        raise HTTPException(status_code=404, detail="Glyph not found.")

    glyph.user_confirmed = body.user_confirmed
    if body.corrected_char_key:
        glyph.char_key = body.corrected_char_key
        glyph.needs_review = False
    db.commit()
    db.refresh(glyph)
    return glyph

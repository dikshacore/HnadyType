from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, HandwritingProfile, GlyphVariant, WordCrop
from app.schemas import GenerateRequest
from app.services.renderer import UserGlyphLibrary, GlyphVariant as RendererGlyph, render_text_to_svg

router = APIRouter(prefix="/generate", tags=["generate"])


def _load_library(profile_id: str, db: Session) -> UserGlyphLibrary:
    library = UserGlyphLibrary()

    for row in db.query(GlyphVariant).filter(GlyphVariant.profile_id == profile_id).all():
        # svg_path = storage.download_svg_path(row.svg_key) -- fetch actual path data
        svg_path = "M0 0"  # placeholder
        variant = RendererGlyph(
            svg_path=svg_path,
            width=row.width,
            height=row.height,
            baseline_offset=row.baseline_offset,
            left_bearing=row.left_bearing,
            right_bearing=row.right_bearing,
        )
        library.chars.setdefault(row.char_key, []).append(variant)

    for row in db.query(WordCrop).filter(WordCrop.profile_id == profile_id).all():
        svg_path = "M0 0"  # placeholder
        library.words[row.text] = RendererGlyph(
            svg_path=svg_path, width=row.width, height=row.height, baseline_offset=row.baseline_offset,
        )

    return library


@router.post("")
def generate(body: GenerateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = (
        db.query(HandwritingProfile)
        .filter(HandwritingProfile.id == body.profile_id, HandwritingProfile.user_id == user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Handwriting profile not found.")

    library = _load_library(profile.id, db)
    if not library.chars:
        raise HTTPException(status_code=422, detail="This profile has no captured handwriting yet -- complete enrollment first.")

    drawing = render_text_to_svg(body.text, library, ink_color=body.ink_color)

    if body.output_format == "svg":
        return Response(content=drawing.tostring(), media_type="image/svg+xml")

    # PNG/PDF export: rasterize the SVG (e.g. via cairosvg) before returning.
    raise HTTPException(status_code=501, detail=f"Output format '{body.output_format}' not wired up yet -- svg works today.")

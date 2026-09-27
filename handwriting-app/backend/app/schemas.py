from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SheetUploadOut(BaseModel):
    sheet_id: str
    sheet_index: int
    status: str


class SheetStatusOut(BaseModel):
    sheet_id: str
    sheet_index: int
    status: str
    error_message: str | None = None


class GlyphOut(BaseModel):
    id: str
    char_key: str
    svg_key: str
    raster_key: str | None
    classifier_confidence: float | None
    needs_review: bool
    user_confirmed: bool

    class Config:
        from_attributes = True


class GlyphReviewUpdate(BaseModel):
    user_confirmed: bool
    corrected_char_key: str | None = None  # set if the user re-labels the glyph


class GenerateRequest(BaseModel):
    profile_id: str
    text: str
    ink_color: str = "#1a1a2e"  # deferred feature, but accepted now so the API is stable
    output_format: str = "png"  # png | pdf | svg

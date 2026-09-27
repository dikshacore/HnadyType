import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey, Enum, Boolean, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profiles = relationship("HandwritingProfile", back_populates="user")


class HandwritingProfile(Base):
    """
    A user can eventually have multiple handwriting profiles
    (e.g. "neat" vs "quick notes"). v1 just creates one default profile
    per user at signup.
    """
    __tablename__ = "handwriting_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    name = Column(String, default="My handwriting")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="profiles")
    sheets = relationship("EnrollmentSheet", back_populates="profile")
    glyphs = relationship("GlyphVariant", back_populates="profile")
    words = relationship("WordCrop", back_populates="profile")


class SheetStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class EnrollmentSheet(Base):
    """One of the 3 fixed-sentence sheets a user fills in and uploads."""
    __tablename__ = "enrollment_sheets"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    profile_id = Column(UUID(as_uuid=False), ForeignKey("handwriting_profiles.id"), nullable=False)
    sheet_index = Column(Integer, nullable=False)  # 0, 1, 2 -> sheet A/B/C
    raw_image_key = Column(String, nullable=False)  # storage key of the uploaded photo
    rectified_image_key = Column(String, nullable=True)  # after perspective correction
    status = Column(Enum(SheetStatus), default=SheetStatus.uploaded)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("HandwritingProfile", back_populates="sheets")


class GlyphVariant(Base):
    """
    One captured instance of one character, e.g. the 2nd 'a' this user
    ever wrote. A character typically ends up with 3+ rows here across
    the 3 enrollment sheets.
    """
    __tablename__ = "glyph_variants"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    profile_id = Column(UUID(as_uuid=False), ForeignKey("handwriting_profiles.id"), nullable=False)
    sheet_id = Column(UUID(as_uuid=False), ForeignKey("enrollment_sheets.id"), nullable=False)

    char_key = Column(String, nullable=False, index=True)  # e.g. "a_lower", "A_upper", "5", "at_sign"
    svg_key = Column(String, nullable=False)  # storage key of vectorized glyph
    raster_key = Column(String, nullable=True)  # storage key of raw crop, for review UI

    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    baseline_offset = Column(Float, nullable=False)
    left_bearing = Column(Float, default=0.0)
    right_bearing = Column(Float, default=0.0)

    classifier_confidence = Column(Float, nullable=True)
    needs_review = Column(Boolean, default=False)
    user_confirmed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("HandwritingProfile", back_populates="glyphs")


class WordCrop(Base):
    """
    Whole-word (or bigram) joined crops kept alongside individual glyphs,
    used to avoid the "stitched letters look robotic" problem — see
    svgRenderer word-lookup-first strategy on the frontend.
    """
    __tablename__ = "word_crops"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    profile_id = Column(UUID(as_uuid=False), ForeignKey("handwriting_profiles.id"), nullable=False)
    sheet_id = Column(UUID(as_uuid=False), ForeignKey("enrollment_sheets.id"), nullable=False)

    text = Column(String, nullable=False, index=True)  # ground-truth word/bigram, lowercased
    svg_key = Column(String, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    baseline_offset = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("HandwritingProfile", back_populates="words")

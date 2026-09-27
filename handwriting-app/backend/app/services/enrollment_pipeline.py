"""
Runs as a background task right after a sheet is uploaded. This is the
"scanning process" from the technical approach turned into code: rectify ->
binarize -> segment lines/words -> align each word to its known ground
truth -> oversegment+align characters -> vectorize -> store, flagging
low-confidence crops for the review screen instead of silently trusting or
silently discarding them.
"""
import cv2
import numpy as np

from app.database import SessionLocal
from app.models import EnrollmentSheet, SheetStatus, GlyphVariant, WordCrop
from app.enrollment_content import all_words_by_sheet
from app.services import preprocessing, segmentation, classifier
from app.services.vectorize import raster_to_svg_path  # see services/vectorize.py
from app.config import settings

_classifier = classifier.ConfidenceClassifier()  # model_path=... once trained


def process_sheet(sheet_id: str) -> None:
    db = SessionLocal()
    try:
        sheet = db.query(EnrollmentSheet).filter(EnrollmentSheet.id == sheet_id).first()
        if not sheet:
            return

        sheet.status = SheetStatus.processing
        db.commit()

        # raw_bytes = storage.download(sheet.raw_image_key)  -- wire up your storage client
        # raw_image = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
        raw_image = _placeholder_load(sheet.raw_image_key)

        binary = preprocessing.preprocess_sheet(raw_image)

        line_boxes = segmentation.segment_lines(binary)
        expected_words = all_words_by_sheet()[sheet.sheet_index]
        word_cursor = 0

        for line_box in line_boxes:
            line_crop = segmentation.crop(binary, line_box)
            word_boxes = segmentation.segment_words(line_crop)

            for word_box in word_boxes:
                if word_cursor >= len(expected_words):
                    break  # more detected word-blobs than expected -- likely noise; skip

                ground_truth_word = expected_words[word_cursor]
                word_cursor += 1

                word_crop = segmentation.crop(line_crop, word_box)
                _store_word_crop(db, sheet, ground_truth_word, word_crop)

                char_boxes = segmentation.align_to_ground_truth(word_crop, ground_truth_word)
                for ch, char_box in zip(ground_truth_word, char_boxes):
                    char_crop = segmentation.crop(word_crop, char_box)
                    _store_glyph(db, sheet, ch, char_crop)

        sheet.status = SheetStatus.processed
        db.commit()

    except Exception as exc:  # noqa: BLE001 -- surface any failure to the user via status
        sheet.status = SheetStatus.failed
        sheet.error_message = str(exc)
        db.commit()
    finally:
        db.close()


def _store_glyph(db, sheet: EnrollmentSheet, ch: str, char_crop: np.ndarray) -> None:
    from app.services.renderer import char_key  # local import avoids a circular import

    svg_path = raster_to_svg_path(char_crop)
    check = _classifier.check_against_expected(char_crop, ch, settings.classifier_confidence_threshold)

    # svg_key = storage.upload_svg(f"users/.../glyphs/{uuid4()}.svg", svg_path)
    svg_key = "placeholder-svg-key"
    raster_key = "placeholder-raster-key"  # keep the raw crop too, for the review UI

    glyph = GlyphVariant(
        profile_id=sheet.profile_id,
        sheet_id=sheet.id,
        char_key=char_key(ch),
        svg_key=svg_key,
        raster_key=raster_key,
        width=float(char_crop.shape[1]),
        height=float(char_crop.shape[0]),
        baseline_offset=float(char_crop.shape[0]),  # refine using ruled-line position later
        classifier_confidence=check["confidence"],
        needs_review=check["needs_review"],
    )
    db.add(glyph)


def _store_word_crop(db, sheet: EnrollmentSheet, word: str, word_crop: np.ndarray) -> None:
    svg_path = raster_to_svg_path(word_crop)
    # svg_key = storage.upload_svg(...)
    svg_key = "placeholder-svg-key"

    db.add(WordCrop(
        profile_id=sheet.profile_id,
        sheet_id=sheet.id,
        text=word.lower(),
        svg_key=svg_key,
        width=float(word_crop.shape[1]),
        height=float(word_crop.shape[0]),
        baseline_offset=float(word_crop.shape[0]),
    ))


def _placeholder_load(image_key: str) -> np.ndarray:
    """Replace with a real storage.download() call. Kept separate so the
    happy-path pipeline logic above stays readable and storage-agnostic."""
    raise NotImplementedError("Wire up object storage download in place of this placeholder.")

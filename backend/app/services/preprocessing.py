"""
Preprocessing pipeline for a photographed/scanned enrollment sheet.

Order matters: fiducial-marker perspective correction must happen before
deskew/binarization, since it's what makes baseline-line detection reliable
downstream in segmentation.py.
"""
import cv2
import numpy as np


def find_fiducial_corners(image: np.ndarray) -> np.ndarray | None:
    """
    Locate the 4 solid black square markers printed in the corners of the
    enrollment sheet template (see enrollment_sheets/generate_sheets.py).
    Returns the 4 corner points ordered [top-left, top-right, bottom-right,
    bottom-left], or None if fewer/more than 4 plausible markers are found.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    img_area = image.shape[0] * image.shape[1]
    for c in contours:
        area = cv2.contourArea(c)
        # Fiducials are small solid squares -- filter by area and shape
        if not (0.0005 * img_area < area < 0.01 * img_area):
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.03 * peri, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect = w / float(h)
            if 0.85 < aspect < 1.15:  # roughly square
                cx, cy = x + w / 2, y + h / 2
                candidates.append((cx, cy))

    if len(candidates) != 4:
        return None

    candidates = np.array(candidates, dtype=np.float32)
    # Order corners: top-left has smallest sum, bottom-right largest sum;
    # top-right has smallest diff, bottom-left largest diff.
    s = candidates.sum(axis=1)
    diff = np.diff(candidates, axis=1).flatten()
    ordered = np.zeros((4, 2), dtype=np.float32)
    ordered[0] = candidates[np.argmin(s)]        # top-left
    ordered[2] = candidates[np.argmax(s)]        # bottom-right
    ordered[1] = candidates[np.argmin(diff)]     # top-right
    ordered[3] = candidates[np.argmax(diff)]     # bottom-left
    return ordered


def rectify_sheet(image: np.ndarray, target_size: tuple[int, int] = (1240, 1754)) -> np.ndarray:
    """
    Perspective-warp the photographed sheet to a flat top-down rectangle
    using the 4 fiducial markers, so ruled baselines are horizontal and at
    known, predictable pixel positions for segmentation.py.
    Falls back to a plain deskew if fiducials aren't found (e.g. a very
    tight crop), so the pipeline degrades gracefully rather than failing.
    """
    corners = find_fiducial_corners(image)
    w, h = target_size

    if corners is None:
        return deskew_only(image)

    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(corners, dst)
    return cv2.warpPerspective(image, matrix, (w, h))


def deskew_only(image: np.ndarray) -> np.ndarray:
    """Fallback: rotate to correct small skew using the dominant text angle."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 100:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    (h, w) = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def binarize(image: np.ndarray) -> np.ndarray:
    """Adaptive binarization -- robust to uneven phone-camera lighting."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, blockSize=25, C=15
    )


def clean_noise(binary_image: np.ndarray) -> np.ndarray:
    """Morphological open+close to remove speckle noise without eroding strokes."""
    kernel = np.ones((2, 2), np.uint8)
    opened = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    return closed


def preprocess_sheet(raw_image: np.ndarray) -> np.ndarray:
    """Full preprocessing pipeline: rectify -> binarize -> denoise."""
    rectified = rectify_sheet(raw_image)
    binary = binarize(rectified)
    return clean_noise(binary)

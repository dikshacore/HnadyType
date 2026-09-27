"""
Segmentation + alignment.

Key design decision from the technical approach: we do NOT need general
handwriting recognition here, because the ground-truth text of every
enrollment sheet is known in advance. We only need to *align* detected ink
segments to the expected characters -- which is far more reliable than
classification, and gives every segment a label "for free".
"""
import numpy as np
import cv2
from dataclasses import dataclass


@dataclass
class BBox:
    x: int
    y: int
    w: int
    h: int


@dataclass
class Segment:
    bbox: BBox
    crop: np.ndarray


def segment_lines(binary_image: np.ndarray, min_line_height: int = 15) -> list[BBox]:
    """Horizontal projection profile -> row bands containing ink."""
    row_sums = binary_image.sum(axis=1)
    in_line = row_sums > 0
    lines = []
    start = None
    for y, has_ink in enumerate(in_line):
        if has_ink and start is None:
            start = y
        elif not has_ink and start is not None:
            if y - start >= min_line_height:
                lines.append(BBox(0, start, binary_image.shape[1], y - start))
            start = None
    if start is not None:
        lines.append(BBox(0, start, binary_image.shape[1], len(in_line) - start))
    return lines


def segment_words(line_crop: np.ndarray, word_gap_multiplier: float = 2.5) -> list[BBox]:
    """
    Vertical projection profile on a single line -> word bands.
    Word gaps are reliably wider than intra-word letter gaps, so we compute
    the median gap width first and use it to set a per-line threshold rather
    than a hardcoded pixel value (handles different handwriting sizes).
    """
    col_sums = line_crop.sum(axis=0)
    has_ink = col_sums > 0

    gaps = []
    runs = []  # (start, end, has_ink)
    start = 0
    current = has_ink[0]
    for x in range(1, len(has_ink)):
        if has_ink[x] != current:
            runs.append((start, x, current))
            start = x
            current = has_ink[x]
    runs.append((start, len(has_ink), current))

    gap_widths = [end - start for start, end, ink in runs if not ink]
    median_gap = np.median(gap_widths) if gap_widths else 5
    word_gap_threshold = median_gap * word_gap_multiplier

    words = []
    word_start = None
    for start, end, ink in runs:
        if ink and word_start is None:
            word_start = start
        elif not ink and word_start is not None and (end - start) > word_gap_threshold:
            words.append(BBox(word_start, 0, start - word_start, line_crop.shape[0]))
            word_start = None
    if word_start is not None:
        words.append(BBox(word_start, 0, len(has_ink) - word_start, line_crop.shape[0]))
    return words


def oversegment_characters(word_crop: np.ndarray) -> list[int]:
    """
    Find all plausible cut points within a word via vertical-projection
    local minima. For printed/block writing these are usually the real
    letter boundaries; for cursive this deliberately over-segments, and
    align_to_ground_truth() below picks the right subset.
    """
    col_sums = word_crop.sum(axis=0).astype(float)
    smoothed = np.convolve(col_sums, np.ones(3) / 3, mode="same")
    cut_points = []
    for x in range(1, len(smoothed) - 1):
        if smoothed[x] <= smoothed[x - 1] and smoothed[x] <= smoothed[x + 1] and smoothed[x] < smoothed.mean() * 0.3:
            cut_points.append(x)
    return cut_points


def align_to_ground_truth(word_crop: np.ndarray, ground_truth_word: str) -> list[BBox]:
    """
    DP/Viterbi-style alignment: given N candidate cut points and a known
    target character count, choose the (len(ground_truth_word) - 1) cuts
    that best match expected per-character width priors.

    This is intentionally a width-prior heuristic for v1, not a learned
    model -- it's cheap, explainable, and works well once you have several
    hundred labeled crops to derive per-character average widths from
    (store those stats and feed them back in as `char_width_priors`).
    """
    n_chars = len(ground_truth_word)
    width = word_crop.shape[1]
    if n_chars == 1:
        return [BBox(0, 0, width, word_crop.shape[0])]

    candidates = oversegment_characters(word_crop)
    ideal_cuts = [round(width * i / n_chars) for i in range(1, n_chars)]

    if len(candidates) < len(ideal_cuts):
        # Not enough natural gaps found (heavily joined cursive) -- fall
        # back to even split; still yields a usable, if imperfect, crop
        # for review/re-flagging by the user.
        chosen_cuts = ideal_cuts
    else:
        # Pick the candidate closest to each ideal cut position (DP would
        # jointly optimize this across all cuts; greedy nearest-match is a
        # reasonable v1 approximation given the small n here).
        chosen_cuts = []
        remaining = candidates.copy()
        for ideal in ideal_cuts:
            best = min(remaining, key=lambda c: abs(c - ideal))
            chosen_cuts.append(best)
            remaining.remove(best)
        chosen_cuts.sort()

    bounds = [0] + chosen_cuts + [width]
    return [
        BBox(bounds[i], 0, bounds[i + 1] - bounds[i], word_crop.shape[0])
        for i in range(n_chars)
    ]


def crop(image: np.ndarray, bbox: BBox) -> np.ndarray:
    return image[bbox.y: bbox.y + bbox.h, bbox.x: bbox.x + bbox.w]

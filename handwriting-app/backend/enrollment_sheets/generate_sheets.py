"""
Generates the printable PDF enrollment sheets.

Layout decisions and why:
  - 4 solid black square fiducial markers in the corners: these are what
    preprocessing.find_fiducial_corners() detects to perspective-correct a
    photographed sheet back to a flat rectangle, so ruled baselines land
    at known, predictable pixel positions downstream.
  - 3 ruled guide lines per writing row (baseline, x-height, ascender/
    descender guides): this gives segmentation/normalization a reliable
    reference for baseline_offset instead of having to infer it from ink
    alone.
  - Each line is printed with faint guide text above it so users copy
    the exact known sentence -- this is what makes ground-truth alignment
    possible without a recognition model.

Run: python generate_sheets.py -> outputs sheet_1.pdf, sheet_2.pdf, sheet_3.pdf
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from app.enrollment_content import SHEETS

PAGE_W, PAGE_H = A4
MARKER_SIZE = 10 * mm
MARGIN = 15 * mm

ROW_HEIGHT = 34 * mm
BASELINE_FROM_TOP = 18 * mm  # within a row, where the writing baseline sits
XHEIGHT_ABOVE_BASELINE = 8 * mm
ASCENDER_ABOVE_BASELINE = 14 * mm
DESCENDER_BELOW_BASELINE = 6 * mm


def draw_fiducial_markers(c: canvas.Canvas):
    """Solid black squares in all 4 corners -- detected by
    preprocessing.find_fiducial_corners() for perspective correction."""
    positions = [
        (MARGIN, PAGE_H - MARGIN - MARKER_SIZE),                       # top-left
        (PAGE_W - MARGIN - MARKER_SIZE, PAGE_H - MARGIN - MARKER_SIZE),  # top-right
        (PAGE_W - MARGIN - MARKER_SIZE, MARGIN),                        # bottom-right
        (MARGIN, MARGIN),                                               # bottom-left
    ]
    c.setFillColorRGB(0, 0, 0)
    for x, y in positions:
        c.rect(x, y, MARKER_SIZE, MARKER_SIZE, fill=1, stroke=0)


def draw_ruled_row(c: canvas.Canvas, top_y: float, guide_text: str):
    """One writing row: faint guide text + 3 horizontal ruled lines."""
    baseline_y = top_y - BASELINE_FROM_TOP

    # Faint guide text sits clear above the ascender line, so it never
    # collides with the ruled guides the user writes against below it.
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    c.drawString(MARGIN + 4 * mm, baseline_y + ASCENDER_ABOVE_BASELINE + 5 * mm, guide_text)

    # Ruled guide lines: ascender, x-height, baseline, descender
    c.setStrokeColorRGB(0.75, 0.8, 0.9)
    c.setLineWidth(0.4)
    for offset in (ASCENDER_ABOVE_BASELINE, XHEIGHT_ABOVE_BASELINE, 0, -DESCENDER_BELOW_BASELINE):
        y = baseline_y + offset
        c.line(MARGIN + 4 * mm, y, PAGE_W - MARGIN - 4 * mm, y)

    # Baseline itself drawn heavier -- this is the primary reference line
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.setLineWidth(0.8)
    c.line(MARGIN + 4 * mm, baseline_y, PAGE_W - MARGIN - 4 * mm, baseline_y)


def generate_sheet_pdf(sheet: dict, output_path: str):
    c = canvas.Canvas(output_path, pagesize=A4)

    draw_fiducial_markers(c)

    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(MARGIN + MARKER_SIZE + 6 * mm, PAGE_H - MARGIN - 8 * mm, sheet["title"])

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(
        MARGIN + MARKER_SIZE + 6 * mm, PAGE_H - MARGIN - 14 * mm,
        "Write each line by hand directly below the guide text, resting letters on the dark baseline.",
    )

    top_y = PAGE_H - MARGIN - MARKER_SIZE - 20 * mm
    for line in sheet["lines"]:
        # Two empty writing rows per guide line: enough vertical space for a
        # natural hand, while the guide text stays fixed so the ground truth
        # is unambiguous.
        draw_ruled_row(c, top_y, line)
        top_y -= ROW_HEIGHT

    c.showPage()
    c.save()


def main():
    out_dir = os.path.dirname(__file__)
    for sheet in SHEETS:
        path = os.path.join(out_dir, f"sheet_{sheet['sheet_index'] + 1}.pdf")
        generate_sheet_pdf(sheet, path)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

"""
Single source of truth for what's printed on each enrollment sheet.
Used by:
  - enrollment_sheets/generate_sheets.py  (renders the PDF the user prints)
  - services/enrollment_pipeline.py       (ground truth for DP alignment)

Based on the 3-sheet set already validated for full-coverage: each sheet
independently covers all 26 letters (upper + lower), 0-9, and the full
punctuation/special-character set -- but through *different* sentences, so
the same letter is captured 3 times in different neighboring-letter
contexts (this is what gives natural per-letter variation instead of 3
identical copies of one line).
"""

SHEETS: list[dict] = [
    {
        "sheet_index": 0,
        "title": "Sheet 1 of 3",
        "lines": [
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "abcdefghijklmnopqrstuvwxyz",
            "The quick brown fox jumps over the lazy dog.",
            "Pack my box with five dozen liquor jugs.",
        ],
    },
    {
        "sheet_index": 1,
        "title": "Sheet 2 of 3",
        "lines": [
            "JACK'S QUIET FOX JUMPED OVER 5 LAZY DOGS.",
            "My 2nd project costs \u20b9500.00 \u2014 really?!",
            "0123456789",
            ".,!?;:'\"-_()[]{}/@#$%&*+=",
        ],
    },
    {
        "sheet_index": 2,
        "title": "Sheet 3 of 3",
        "lines": [
            "Sphinx of black quartz, judge my vow!",
            "How vexingly quick daft zebras jump.",
            "Item #42: qty 7 @ $3.98 = $27.86 (tax incl.)",
            "waltz, nymph; cwm fjord-bank glyphs vext quiz.",
        ],
    },
]


def all_words_by_sheet() -> dict[int, list[str]]:
    """Flat list of ground-truth words per sheet, in reading order -- what
    segmentation.align_to_ground_truth() zips against detected word crops."""
    result = {}
    for sheet in SHEETS:
        words = []
        for line in sheet["lines"]:
            words.extend(line.split(" "))
        result[sheet["sheet_index"]] = words
    return result

"""
Option A renderer (glyph stitching), mirrored server-side so PDF/PNG export
matches the client-side live preview exactly. See frontend/lib/svgRenderer.ts
for the browser version used for instant preview.

Resolution order per token: whole word crop -> bigram crops -> single
glyphs. This is the concrete fix for "treating each character independently
disturbs the writing flow": real joined ink is used wherever we have it,
and stitching is only a fallback for text the user never wrote.
"""
import random
import svgwrite
from dataclasses import dataclass


@dataclass
class GlyphVariant:
    svg_path: str
    width: float
    height: float
    baseline_offset: float
    left_bearing: float = 0.0
    right_bearing: float = 0.0


class UserGlyphLibrary:
    def __init__(self):
        self.chars: dict[str, list[GlyphVariant]] = {}
        self.words: dict[str, GlyphVariant] = {}
        self.bigrams: dict[str, GlyphVariant] = {}
        self._last_variant_index: dict[str, int] = {}

    def pick_variant(self, char_key: str) -> GlyphVariant | None:
        variants = self.chars.get(char_key)
        if not variants:
            return None
        if len(variants) == 1:
            return variants[0]
        # Avoid repeating the same variant back-to-back so identical letters
        # in a row don't look copy-pasted.
        last_idx = self._last_variant_index.get(char_key, -1)
        choices = [i for i in range(len(variants)) if i != last_idx]
        idx = random.choice(choices)
        self._last_variant_index[char_key] = idx
        return variants[idx]


def char_key(ch: str) -> str:
    if ch.isalpha():
        return f"{ch.lower()}_{'upper' if ch.isupper() else 'lower'}"
    named = {
        ".": "period", ",": "comma", "!": "bang", "?": "question", ";": "semicolon",
        ":": "colon", "'": "apostrophe", '"': "quote", "-": "hyphen", "_": "underscore",
        "(": "lparen", ")": "rparen", "[": "lbracket", "]": "rbracket",
        "{": "lbrace", "}": "rbrace", "/": "slash", "@": "at", "#": "hash",
        "$": "dollar", "%": "percent", "&": "amp", "*": "star", "+": "plus", "=": "equals",
    }
    return named.get(ch, f"char_{ord(ch)}")


def stitch_word(word: str, library: UserGlyphLibrary, jitter_deg: float = 1.5, baseline_wobble_px: float = 2.0):
    """Returns a list of (GlyphVariant, x_offset, y_offset, rotation_deg)."""
    placements = []
    cursor_x = 0.0
    i = 0
    lower = word.lower()
    while i < len(word):
        bigram_key = lower[i:i + 2]
        bigram = library.bigrams.get(bigram_key) if len(bigram_key) == 2 else None
        if bigram:
            y_wobble = random.uniform(-baseline_wobble_px, baseline_wobble_px)
            placements.append((bigram, cursor_x, y_wobble, 0.0))
            cursor_x += bigram.width + bigram.right_bearing
            i += 2
            continue

        variant = library.pick_variant(char_key(word[i]))
        if variant is None:
            variant = library.pick_variant("fallback")  # generic unseen-char glyph
        if variant:
            rotation = random.uniform(-jitter_deg, jitter_deg)
            y_wobble = random.uniform(-baseline_wobble_px, baseline_wobble_px)
            placements.append((variant, cursor_x, y_wobble, rotation))
            cursor_x += variant.width + variant.right_bearing
        i += 1
    return placements, cursor_x


def render_text_to_svg(text: str, library: UserGlyphLibrary, ink_color: str = "#1a1a2e",
                        line_height: float = 60.0, max_width: float = 780.0) -> svgwrite.Drawing:
    words = text.split(" ")
    dwg = svgwrite.Drawing(size=(max_width, 100))  # height grows as we lay out lines
    cursor_x, cursor_y = 20.0, 40.0
    total_height = 100.0

    for word in words:
        lower = word.lower()
        if lower in library.words:
            variant = library.words[lower]
            placements, advance = [(variant, 0.0, 0.0, 0.0)], variant.width
        else:
            placements, advance = stitch_word(word, library)

        if cursor_x + advance > max_width:
            cursor_x = 20.0
            cursor_y += line_height
            total_height += line_height

        group = dwg.g(fill=ink_color)
        for variant, x_off, y_off, rotation in placements:
            transform = f"translate({cursor_x + x_off},{cursor_y + y_off}) rotate({rotation})"
            group.add(dwg.path(d=variant.svg_path, transform=transform))
        dwg.add(group)

        cursor_x += advance + 14  # inter-word space

    dwg.attribs["height"] = total_height + 40
    dwg.attribs["viewBox"] = f"0 0 {max_width} {total_height + 40}"
    return dwg

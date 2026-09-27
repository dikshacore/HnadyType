/**
 * Client-side glyph composition for the live "type and see your
 * handwriting" preview. Mirrors backend/app/services/renderer.py exactly
 * so what the user sees while typing matches the exported file.
 *
 * Resolution order per token: whole word crop -> bigram crops -> single
 * glyph stitching. This is the concrete fix for "treating each character
 * independently disturbs the writing flow" -- real joined ink is used
 * wherever it exists, stitching is only a fallback.
 */

export interface GlyphVariant {
  svgPath: string;
  width: number;
  height: number;
  baselineOffset: number;
  leftBearing: number;
  rightBearing: number;
}

export interface UserGlyphLibrary {
  chars: Record<string, GlyphVariant[]>;
  words: Record<string, GlyphVariant>;
  bigrams: Record<string, GlyphVariant>;
}

export interface Placement {
  variant: GlyphVariant;
  x: number;
  y: number;
  rotationDeg: number;
}

const lastVariantIndex: Record<string, number> = {};

export function charKey(ch: string): string {
  if (/[a-zA-Z]/.test(ch)) {
    return `${ch.toLowerCase()}_${ch === ch.toUpperCase() ? "upper" : "lower"}`;
  }
  const named: Record<string, string> = {
    ".": "period", ",": "comma", "!": "bang", "?": "question", ";": "semicolon",
    ":": "colon", "'": "apostrophe", '"': "quote", "-": "hyphen", "_": "underscore",
    "(": "lparen", ")": "rparen", "[": "lbracket", "]": "rbracket",
    "{": "lbrace", "}": "rbrace", "/": "slash", "@": "at", "#": "hash",
    "$": "dollar", "%": "percent", "&": "amp", "*": "star", "+": "plus", "=": "equals",
  };
  return named[ch] ?? `char_${ch.charCodeAt(0)}`;
}

function pickVariant(library: UserGlyphLibrary, key: string): GlyphVariant | null {
  const variants = library.chars[key];
  if (!variants || variants.length === 0) return null;
  if (variants.length === 1) return variants[0];

  const lastIdx = lastVariantIndex[key] ?? -1;
  const choices = variants.map((_, i) => i).filter((i) => i !== lastIdx);
  const idx = choices[Math.floor(Math.random() * choices.length)];
  lastVariantIndex[key] = idx;
  return variants[idx];
}

function stitchWord(
  word: string,
  library: UserGlyphLibrary,
  jitterDeg = 1.5,
  baselineWobblePx = 2
): { placements: Placement[]; advance: number } {
  const placements: Placement[] = [];
  let cursorX = 0;
  const lower = word.toLowerCase();
  let i = 0;

  while (i < word.length) {
    const bigramKey = lower.slice(i, i + 2);
    const bigram = bigramKey.length === 2 ? library.bigrams[bigramKey] : undefined;

    if (bigram) {
      const y = (Math.random() * 2 - 1) * baselineWobblePx;
      placements.push({ variant: bigram, x: cursorX, y, rotationDeg: 0 });
      cursorX += bigram.width + bigram.rightBearing;
      i += 2;
      continue;
    }

    const variant = pickVariant(library, charKey(word[i])) ?? pickVariant(library, "fallback");
    if (variant) {
      const rotation = (Math.random() * 2 - 1) * jitterDeg;
      const y = (Math.random() * 2 - 1) * baselineWobblePx;
      placements.push({ variant, x: cursorX, y, rotationDeg: rotation });
      cursorX += variant.width + variant.rightBearing;
    }
    i += 1;
  }

  return { placements, advance: cursorX };
}

export interface RenderedLine {
  placements: Placement[];
  advance: number;
  isWholeWord: boolean;
}

/** Lays out full text into positioned glyph placements the caller renders as SVG. */
export function renderText(text: string, library: UserGlyphLibrary, maxWidth = 780): {
  lines: { y: number; words: RenderedLine[] }[];
  totalHeight: number;
} {
  const lineHeight = 60;
  const words = text.split(" ");

  const lines: { y: number; words: RenderedLine[] }[] = [{ y: 40, words: [] }];
  let cursorX = 20;

  for (const word of words) {
    const lower = word.toLowerCase();
    let result: RenderedLine;

    if (library.words[lower]) {
      const v = library.words[lower];
      result = { placements: [{ variant: v, x: 0, y: 0, rotationDeg: 0 }], advance: v.width, isWholeWord: true };
    } else {
      const { placements, advance } = stitchWord(word, library);
      result = { placements, advance, isWholeWord: false };
    }

    if (cursorX + result.advance > maxWidth) {
      cursorX = 20;
      lines.push({ y: lines[lines.length - 1].y + lineHeight, words: [] });
    }

    lines[lines.length - 1].words.push({ ...result });
    cursorX += result.advance + 14;
  }

  const totalHeight = lines[lines.length - 1].y + lineHeight;
  return { lines, totalHeight };
}

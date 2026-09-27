"""
Converts a binary raster glyph crop into an SVG path string.

For a real implementation, shell out to `potrace` (via the `pypotrace`
bindings or a subprocess call to the potrace CLI on a temporary PGM/BMP
file) -- it's the standard tool for exactly this and produces clean,
smooth vector outlines from a binary bitmap. Kept as a stub here so the
rest of the pipeline is runnable/testable without that native dependency
installed yet.
"""
import numpy as np


def raster_to_svg_path(binary_crop: np.ndarray) -> str:
    # Real version:
    #   1. Write binary_crop to a temp PBM/BMP file
    #   2. subprocess.run(["potrace", "-s", "-o", out_svg, temp_path])
    #   3. Parse the <path d="..."> out of the produced SVG and return it
    raise NotImplementedError("Wire up potrace (or an equivalent tracer) here.")

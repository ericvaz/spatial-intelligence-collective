#!/usr/bin/env python3
"""Turn a scanned alphabet sheet into a webfont.

Source: a single sheet with A-Z on three rows and a-z on three more, written
with a marker on white paper. Each glyph is cut out by projection, traced with
marching squares, simplified, and dropped into a TrueType font.

    python3 tools/build_font.py ~/Desktop/unnamed-1.png

Writes assets/fonts/vazhand.woff2 (and .ttf next to it for reference).
"""

import sys
import pathlib

import numpy as np
from PIL import Image
import contourpy
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

ROWS = ["ABCDEFGHI", "JKLMNOPQ", "RSTUVWXYZ",
        "abcdefghi", "jklmnopq", "rstuvwxyz"]

UPM = 1000          # units per em
CAP = 700           # cap height in units
SUPERSAMPLE = 3     # upscale before tracing, for smoother contours
RDP_TOL = 3.5       # outline simplification, in font units
SIDE_BEARING = 0.05  # per side, as a fraction of the em
SPACE = 0.30        # space advance, as a fraction of the em

OUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "assets" / "fonts"
NAME = "Vaz Hand"
PSNAME = "VazHand-Regular"


# ---------------------------------------------------------------- segmenting

def bands(mask, axis, min_size, gap):
    """Runs of non-empty rows (axis=1) or columns (axis=0), merged across gaps."""
    on = mask.any(axis=axis)
    runs, start = [], None
    for i, v in enumerate(on):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(on) - 1))
    runs = [r for r in runs if r[1] - r[0] + 1 >= min_size]
    merged = [runs[0]]
    for a, b in runs[1:]:
        if a - merged[-1][1] < gap:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def cut_sheet(gray):
    """-> {char: (x0, x1, y0, y1, baseline)} in source pixels."""
    ink = gray < 128
    row_bands = bands(ink, 1, 10, 12)
    if len(row_bands) != len(ROWS):
        sys.exit("expected %d rows, found %d" % (len(ROWS), len(row_bands)))

    boxes = {}
    for letters, (y0, y1) in zip(ROWS, row_bands):
        strip = ink[y0:y1 + 1]
        cols = bands(strip, 0, 3, 12)
        if len(cols) != len(letters):
            sys.exit("row %r: expected %d glyphs, found %d"
                     % (letters, len(letters), len(cols)))
        cells = []
        for x0, x1 in cols:
            ys = np.where(strip[:, x0:x1 + 1].any(axis=1))[0]
            cells.append((x0, x1, y0 + ys.min(), y0 + ys.max()))
        # letters that sit on the baseline are the majority in every row, so
        # the median bottom edge is the baseline
        baseline = float(np.median([c[3] for c in cells]))
        for ch, (x0, x1, gy0, gy1) in zip(letters, cells):
            boxes[ch] = (x0, x1, gy0, gy1, baseline)
    return boxes


# ---------------------------------------------------------------- vectorising

def rdp(points, tol):
    """Ramer-Douglas-Peucker on an open polyline."""
    if len(points) < 3:
        return points
    p0, p1 = points[0], points[-1]
    d = p1 - p0
    norm = np.hypot(*d)
    if norm < 1e-9:
        dist = np.hypot(*(points - p0).T)
    else:
        dist = np.abs(np.cross(d, points - p0)) / norm
    i = int(np.argmax(dist))
    if dist[i] <= tol:
        return np.array([p0, p1])
    left = rdp(points[:i + 1], tol)
    right = rdp(points[i:], tol)
    return np.vstack([left[:-1], right])


def signed_area(poly):
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def contains(outer, point):
    x, y = point
    xs, ys = outer[:, 0], outer[:, 1]
    xs2, ys2 = np.roll(xs, -1), np.roll(ys, -1)
    crosses = ((ys > y) != (ys2 > y))
    with np.errstate(divide="ignore", invalid="ignore"):
        xint = xs + (y - ys) / (ys2 - ys) * (xs2 - xs)
    return bool(np.sum(crosses & (xint > x)) % 2)


def trace(gray, box, scale):
    """Outlines for one glyph, in font units with the origin on the baseline."""
    x0, x1, gy0, gy1, baseline = box
    pad = 4
    sub = gray[max(0, gy0 - pad):gy1 + pad + 1, max(0, x0 - pad):x1 + pad + 1]
    oy, ox = max(0, gy0 - pad), max(0, x0 - pad)

    big = np.asarray(Image.fromarray(sub).resize(
        (sub.shape[1] * SUPERSAMPLE, sub.shape[0] * SUPERSAMPLE),
        Image.LANCZOS)).astype(np.float32)

    gen = contourpy.contour_generator(z=big, name="serial", line_type="SeparateCode")
    lines, _ = gen.lines(127.5)

    polys = []
    for line in lines:
        if len(line) < 4:
            continue
        # supersampled sub-image pixels -> source pixels -> font units
        px = line[:, 0] / SUPERSAMPLE + ox
        py = line[:, 1] / SUPERSAMPLE + oy
        poly = np.column_stack([(px - x0) * scale, (baseline - py) * scale])
        if np.allclose(poly[0], poly[-1]):
            poly = poly[:-1]
        poly = rdp(np.vstack([poly, poly[0]]), RDP_TOL)[:-1]
        if len(poly) >= 3 and abs(signed_area(poly)) > 200:
            polys.append(poly)

    # nesting depth decides outer vs hole; TrueType wants outers clockwise
    oriented = []
    for i, poly in enumerate(polys):
        depth = sum(1 for j, other in enumerate(polys)
                    if j != i and contains(other, poly[0]))
        want_ccw = depth % 2 == 1
        if (signed_area(poly) > 0) != want_ccw:
            poly = poly[::-1]
        oriented.append(poly)
    return oriented


# ------------------------------------------------------------------ building

def main():
    src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                       else "~/Desktop/unnamed-1.png").expanduser()
    gray = np.asarray(Image.open(src).convert("L")).astype(np.uint8)
    boxes = cut_sheet(gray)

    cap_px = np.median([b[4] - b[2] for ch, b in boxes.items() if ch.isupper()])
    scale = CAP / cap_px
    print("cap height %.1f px -> scale %.4f" % (cap_px, scale))

    sb = round(SIDE_BEARING * UPM)
    glyphs, widths, order = {}, {}, [".notdef", "space"]
    cmap = {0x20: "space"}

    pen = TTGlyphPen(None)
    glyphs[".notdef"] = pen.glyph()
    widths[".notdef"] = round(SPACE * UPM)
    glyphs["space"] = TTGlyphPen(None).glyph()
    widths["space"] = round(SPACE * UPM)

    for ch in sorted(boxes, key=lambda c: (c.islower(), c)):
        gname = ch  # 'A'..'Z' and 'a'..'z' are already valid glyph names
        pen = TTGlyphPen(None)
        polys = trace(gray, boxes[ch], scale)
        for poly in polys:
            pen.moveTo((round(poly[0][0]) + sb, round(poly[0][1])))
            for x, y in poly[1:]:
                pen.lineTo((round(x) + sb, round(y)))
            pen.closePath()
        glyph = pen.glyph()
        widths[gname] = round((boxes[ch][1] - boxes[ch][0]) * scale) + 2 * sb
        glyphs[gname] = glyph
        order.append(gname)
        cmap[ord(ch)] = gname
        print("  %s  %d contours, %d pts, adv %d"
              % (ch, len(polys), sum(len(p) for p in polys), widths[gname]))

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({g: (widths[g], 0) for g in order})
    asc, desc = 800, -260
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0)
    fb.setupNameTable({
        "familyName": NAME, "styleName": "Regular",
        "psName": PSNAME, "version": "Version 1.0",
        "fullName": NAME, "uniqueFontIdentifier": "1.0;%s" % PSNAME,
        "copyright": "Handwriting of Eric Vaz.",
    })
    x_box = boxes["x"]
    x_height = round((x_box[4] - x_box[2]) * scale)
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
                usWinAscent=asc, usWinDescent=-desc, sxHeight=x_height,
                sCapHeight=CAP, achVendID="EVAZ")
    fb.setupPost(isFixedPitch=0)
    fb.setupDummyDSIG()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ttf = OUT_DIR / "vazhand.ttf"
    fb.save(str(ttf))

    fb.font.flavor = "woff2"
    woff2 = OUT_DIR / "vazhand.woff2"
    fb.font.save(str(woff2))
    print("wrote %s (%.1f KB) and %s (%.1f KB)"
          % (ttf.name, ttf.stat().st_size / 1024,
             woff2.name, woff2.stat().st_size / 1024))


if __name__ == "__main__":
    main()

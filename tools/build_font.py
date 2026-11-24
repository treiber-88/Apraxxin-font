"""Build Apraxxin.ttf from the stroke drawings in glyphs.py.

Character mapping (the same glyphs are reachable two ways):
  * Private Use Area: U+E000 + ASCII code  (e.g. 'a' -> U+E061, 'A' -> U+E041, '0' -> U+E030)
    plus U+E080 = closing double quote, U+E081 = em dash.
    These are what the typing tool sends; Windows shows them in every app through the
    EUDC (end-user-defined character) font link.
  * Ordinary ASCII / smart-quote / em-dash code points, so the font can also simply be
    selected as "Apraxxin" in a word processor.

Capital letters = the lowercase glyph with a line above it.

  python tools/build_font.py   -> build/Apraxxin.ttf
"""
import math, os, sys

import pathops
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from geometry import expand  # noqa: E402
import glyphs  # noqa: E402

UPM = 1000
PEN = glyphs.PEN
SIDE = 60            # side bearing
CAP_TOP = 740        # top of a normal glyph
OVERLINE_Y = 830     # centre of the capital-letter line
PUA = 0xE000

# How each glyph is sized/positioned: (mode, max_height[, anchor])
#   base: bottom on the baseline          keep: keep the drawn vertical position (scaled)
#   mid:  centred on the maths axis       top:  top at cap height          span: bracket-like
PLACE = {k: ("base", 740) for k in glyphs.GLYPHS}
PLACE.update({
    "g": ("keep", 1000), "j": ("keep", 1000), "p": ("keep", 1000),
    "colon": ("keep", 1000), "semicolon": ("keep", 1000), "comma": ("keep", 1000),
    "question": ("keep", 800),
    "period": ("base", 480),
    "apostrophe": ("top", 420), "quoteleft": ("top", 320),
    "quotedblleft": ("top", 320), "quotedblright": ("top", 320),
    "asterisk": ("top", 520),
    "plus": ("mid", 560), "equal": ("mid", 560), "hyphen": ("mid", 400), "emdash": ("mid", 480),
    "parenleft": ("span", 1050), "parenright": ("span", 1050),
    "bracketleft": ("span", 1050), "bracketright": ("span", 1050),
    "braceleft": ("span", 1050), "braceright": ("span", 1050),
})
MAX_W = 1000
# extra enlargement for individual glyphs (the user asked for a bigger e)
GROW = {"e": 1.25}

# glyph key -> ASCII character it stands for
ASCII_OF = {c: c for c in "abcdefghijklmnopqrstuvwxyz0123456789"}
ASCII_OF.update({
    "colon": ":", "semicolon": ";", "comma": ",", "apostrophe": "'", "slash": "/",
    "backslash": "\\", "plus": "+", "hyphen": "-", "equal": "=", "quotedblleft": '"',
    "quoteleft": "`", "exclam": "!", "period": ".", "question": "?", "ampersand": "&",
    "asterisk": "*", "parenleft": "(", "parenright": ")", "bracketleft": "[",
    "bracketright": "]", "braceleft": "{", "braceright": "}",
})
EXTRA_PUA = {"quotedblright": 0xE080, "emdash": 0xE081}
# additional standard code points for "select the font in Word" use
STD_EXTRA = {"quotedblleft": [0x201C], "quotedblright": [0x201D], "quoteleft": [0x2018],
             "apostrophe": [0x2019], "emdash": [0x2014, 0x2013]}


def glyph_name(key):
    return key if len(key) > 1 else ("uni%04X" % ord(key) if key.isdigit() else key)


# ---------------------------------------------------------------- outlines
def circle(path, x, y, r):
    k = 0.5522847498 * r
    path.moveTo(x + r, y)
    path.cubicTo(x + r, y + k, x + k, y + r, x, y + r)
    path.cubicTo(x - k, y + r, x - r, y + k, x - r, y)
    path.cubicTo(x - r, y - k, x - k, y - r, x, y - r)
    path.cubicTo(x + k, y - r, x + r, y - k, x + r, y)
    path.close()


def segment(path, a, b, r):
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return
    nx, ny = -dy / L * r, dx / L * r
    pts = [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]
    # keep winding consistent (counter-clockwise)
    area = sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(4))
    if area > 0:
        pts.reverse()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    path.close()


def stroke_path(strokes, transform=lambda x, y: (x, y), extra=()):
    """Union of pen strokes -> pathops.Path (already transformed)."""
    lines, closed, dots = expand(strokes, PEN)
    r = PEN / 2
    path = pathops.Path()
    for line in lines:
        pts = [transform(*p) for p in line]
        for a, b in zip(pts, pts[1:]):
            segment(path, a, b, r)
        for p in pts:
            circle(path, p[0], p[1], r)
    for x, y, dr in dots:
        (tx, ty), (sx, _) = transform(x, y), transform(x + dr, y)
        circle(path, tx, ty, abs(sx - tx))
    for a, b in extra:  # already-transformed straight lines (overline)
        segment(path, a, b, r)
        circle(path, *a, r)
        circle(path, *b, r)
    path.simplify(fix_winding=True)
    return path


def ink_bbox(strokes):
    lines, _, dots = expand(strokes, PEN)
    xs = [p[0] for l in lines for p in l] + [d[0] + s * d[2] for d in dots for s in (-1, 1)]
    ys = [p[1] for l in lines for p in l] + [d[1] + s * d[2] for d in dots for s in (-1, 1)]
    return min(xs), min(ys), max(xs), max(ys)


def placement(key, strokes):
    """-> (scale, dx, dy) so that final = (x*scale+dx, y*scale+dy)."""
    mode, maxh = PLACE[key][:2]
    x0, y0, x1, y1 = ink_bbox(strokes)
    w, h = x1 - x0, y1 - y0
    g = GROW.get(key, 1.0)
    s = min(g, maxh * g / h if h else g, MAX_W * g / w if w else g)
    dx = SIDE + PEN / 2 - x0 * s
    if mode == "base":
        dy = -y0 * s
    elif mode == "keep":
        dy = 0.0
        if y1 * s > CAP_TOP + 60:
            dy = CAP_TOP + 60 - y1 * s
    elif mode == "mid":
        dy = 340 - (y0 + y1) / 2 * s
    elif mode == "top":
        dy = CAP_TOP - y1 * s
    elif mode == "span":
        dy = 290 - (y0 + y1) / 2 * s
    else:
        raise ValueError(mode)
    adv = int(round(w * s + PEN + 2 * SIDE))
    return s, dx, dy, adv, (x0 * s + dx, y0 * s + dy, x1 * s + dx, y1 * s + dy)


def draw_glyph(key, capital=False):
    strokes = glyphs.GLYPHS[key]
    s, dx, dy, adv, (bx0, by0, bx1, by1) = placement(key, strokes)
    T = lambda x, y: (x * s + dx, y * s + dy)
    extra = []
    if capital:
        oy = max(OVERLINE_Y, by1 + PEN + 40)
        extra.append(((bx0, oy), (bx1, oy)))
    path = stroke_path(strokes, T, extra)
    rec = RecordingPen()
    path.draw(rec)
    pen = TTGlyphPen(None)
    rec.replay(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
    return pen.glyph(), adv


# ---------------------------------------------------------------- font
def build(out_path):
    order = [".notdef", "space"]
    glyf, metrics, cmap = {}, {}, {}

    nd = TTGlyphPen(None)
    for (a, b, c, d) in [(50, 0, 450, 700)]:
        nd.moveTo((a, b)); nd.lineTo((a, d)); nd.lineTo((c, d)); nd.lineTo((c, b)); nd.closePath()
        nd.moveTo((a + 50, b + 50)); nd.lineTo((c - 50, b + 50)); nd.lineTo((c - 50, d - 50)); nd.lineTo((a + 50, d - 50)); nd.closePath()
    glyf[".notdef"], metrics[".notdef"] = nd.glyph(), (500, 50)
    glyf["space"], metrics["space"] = TTGlyphPen(None).glyph(), (380, 0)
    cmap[0x20] = "space"
    cmap[PUA + 0x20] = "space"
    cmap[0xA0] = "space"

    def add(name, glyph, adv, codes):
        order.append(name)
        glyf[name] = glyph
        glyph.recalcBounds(glyf)
        metrics[name] = (adv, getattr(glyph, "xMin", 0))
        for c in codes:
            cmap[c] = name

    for key in glyphs.GLYPHS:
        g, adv = draw_glyph(key)
        codes = []
        ch = ASCII_OF.get(key)
        if ch:
            codes += [ord(ch), PUA + ord(ch)]
        if key == "quotedblleft":
            codes += [ord('"')]
        if key in EXTRA_PUA:
            codes.append(EXTRA_PUA[key])
        codes += STD_EXTRA.get(key, [])
        add(glyph_name(key), g, adv, sorted(set(codes)))
        if key.isalpha() and len(key) == 1:
            g2, adv2 = draw_glyph(key, capital=True)
            up = key.upper()
            add(up, g2, adv2, [ord(up), PUA + ord(up)])

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=1000, descent=-320)
    fb.setupNameTable({
        "familyName": "Apraxxin",
        "styleName": "Regular",
        "uniqueFontIdentifier": "Apraxxin-Regular-1.0",
        "fullName": "Apraxxin",
        "psName": "Apraxxin-Regular",
        "version": "Version 1.000",
    })
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, sTypoLineGap=200,
                usWinAscent=1000, usWinDescent=320, sxHeight=500, sCapHeight=740,
                achVendID="APRX", fsType=0)
    fb.setupPost()
    fb.setupDummyDSIG() if hasattr(fb, "setupDummyDSIG") else None
    fb.font["head"].fontRevision = 1.0
    # Fixed timestamps: identical drawings give an identical file, so the installed
    # file name (which includes a hash) only changes when the glyphs really change.
    fb.font["head"].created = fb.font["head"].modified = 3_850_000_000  # 2026, seconds since 1904
    fb.font.recalcTimestamp = False
    fb.save(out_path)
    return len(order)


if __name__ == "__main__":
    out = os.path.join(ROOT, "build", "Apraxxin.ttf")
    n = build(out)
    print("wrote", out, n, "glyphs")

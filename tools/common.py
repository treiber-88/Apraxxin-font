"""Shared helpers: photo -> font-unit mapping for each entry."""
import os, sys
import cv2, numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from sources import ENTRIES, SCALE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = 700  # font units for one handwritten capital height

# Punctuation rows are not reliably on a baseline via their source char, so give
# the baseline (half-res y) explicitly. Everything else uses the src box bottom.
PUNCT_BASELINE = {
    "colon": 515, "semicolon": 515,
    "comma": 712, "apostrophe": 705, "slash": 710,
    "backslash": 893, "plus": 893, "hyphen": 893,
    "equal": 965, "quotedblleft": 1050, "quotedblright": 1040, "quoteleft": 1010,
    "exclam": 1250, "period": 1215, "question": 1212,
    "ampersand": 1460, "asterisk": 1440, "emdash": 1450,
    "parenleft": 1655, "parenright": 1655, "bracketleft": 1650,
    "bracketright": 1880, "braceleft": 1880, "braceright": 1880,
}
_imgs = {}


def image(name):
    if name not in _imgs:
        _imgs[name] = cv2.imread(os.path.join(ROOT, "source", name + "_upright.png"), cv2.IMREAD_GRAYSCALE)
    return _imgs[name]


def cap_px():
    """Median height (full-res px) of the plain source characters per image."""
    out = {}
    for img in {e[1] for e in ENTRIES}:
        if img == "punctuation":
            hs = [(s[3] - s[1]) for k, i, s, g in ENTRIES if k in ("exclam", "question", "ampersand")]
        else:
            hs = [(s[3] - s[1]) for k, i, s, g in ENTRIES if i == img]
        out[img] = float(np.median(hs)) * SCALE
    return out


CAP_PX = cap_px()


class Mapping:
    """Maps full-res photo pixels <-> font units for one entry."""

    def __init__(self, key, img, src, gbox):
        self.key, self.img = key, img
        self.k = CAP / CAP_PX[img]                      # units per px
        base_half = PUNCT_BASELINE.get(key, src[3])
        self.base_y = base_half * SCALE                 # px
        self.left_x = gbox[0] * SCALE                   # px -> x=0 at glyph box left

    def to_units(self, x, y):
        return (x - self.left_x) * self.k, (self.base_y - y) * self.k

    def to_px(self, u, v):
        return u / self.k + self.left_x, self.base_y - v / self.k


def entries():
    for key, img, src, gbox in ENTRIES:
        yield key, img, src, gbox, Mapping(key, img, src, gbox)

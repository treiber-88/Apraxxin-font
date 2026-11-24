"""Drawing/checking tool: shows each source glyph on a font-unit grid with the
stroke drawing from glyphs.py overlaid in red.

  python tools/preview.py            all glyphs -> build/preview/sheet_*.png
  python tools/preview.py a b c      only these keys
"""
import importlib, os, sys
import cv2, numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT, SCALE, entries, image
from geometry import expand

sys.path.insert(0, ROOT)
import glyphs  # noqa: E402  (ROOT/glyphs.py)

OUT = os.path.join(ROOT, "build", "preview")
os.makedirs(OUT, exist_ok=True)
PX_PER_UNIT = float(os.environ.get("ZOOM", "0.45"))


def tile(key, img, gbox, m, strokes, pen):
    pad = 100 * SCALE * 0  # margin in px around the glyph box
    x0, y0, x1, y1 = [v * SCALE for v in gbox]
    mx = 40
    x0, y0, x1, y1 = x0 - mx, y0 - mx, x1 + mx, y1 + mx
    # unit-space window
    u0, v1 = m.to_units(x0, y0)
    u1, v0 = m.to_units(x1, y1)
    u0, v0 = min(u0, -50), min(v0, -50)
    v1 = max(v1, 750)
    u1 = u1 + 60; v1 = v1 + 80; v0 = v0 - 40
    W, H = int((u1 - u0) * PX_PER_UNIT), int((v1 - v0) * PX_PER_UNIT)
    # sample photo through the mapping
    src = image(img)
    xs = np.array([m.to_px(u0 + c / PX_PER_UNIT, 0)[0] for c in range(W)], np.float32)
    ys = np.array([m.to_px(0, v1 - r / PX_PER_UNIT)[1] for r in range(H)], np.float32)
    mapx, mapy = np.meshgrid(xs, ys)
    photo = cv2.remap(src, mapx, mapy, cv2.INTER_AREA)
    canvas = cv2.cvtColor(photo, cv2.COLOR_GRAY2BGR)
    canvas = cv2.normalize(canvas, None, 0, 255, cv2.NORM_MINMAX)
    grid = canvas.copy()
    P = lambda u, v: (int(round((u - u0) * PX_PER_UNIT)), int(round((v1 - v) * PX_PER_UNIT)))
    # grid
    for u in range(int(u0 // 50) * 50, int(u1) + 1, 50):
        if u % 100: continue
        cv2.line(grid, P(u, v0), P(u, v1), (60, 60, 255), 1)
        cv2.putText(canvas, str(u), (P(u, 0)[0] + 2, H - 4), 0, 0.4, (0, 0, 200), 1)
        cv2.putText(canvas, str(u), (P(u, 0)[0] + 2, 12), 0, 0.4, (0, 0, 200), 1)
    for v in range(int(v0 // 50) * 50, int(v1) + 1, 50):
        if v % 100: continue
        c = (0, 160, 0) if v in (0, 700) else (255, 60, 60)
        cv2.line(grid, P(u0, v), P(u1, v), c, 1)
        cv2.putText(canvas, str(v), (2, P(0, v)[1] - 2), 0, 0.4, (200, 0, 0), 1)
    canvas = cv2.addWeighted(canvas, 0.6, grid, 0.4, 0)
    # strokes
    if strokes:
        over = canvas.copy()
        lines, closed, dots = expand(strokes, pen)
        t = max(1, int(pen * PX_PER_UNIT))
        for l in lines:
            pts = np.array([P(*p) for p in l], np.int32)
            cv2.polylines(over, [pts], False, (0, 0, 230), t, cv2.LINE_AA)
        for x, y, r in dots:
            cv2.circle(over, P(x, y), int(r * PX_PER_UNIT), (0, 0, 230), -1, cv2.LINE_AA)
        canvas = cv2.addWeighted(canvas, 0.45, over, 0.55, 0)
        for l in lines:
            for p in l if len(l) < 12 else []:
                cv2.circle(canvas, P(*p), 3, (0, 120, 0), -1)
    canvas = cv2.copyMakeBorder(canvas, 26, 4, 4, 4, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.putText(canvas, key, (4, 20), 0, 0.7, (160, 0, 0), 2)
    return canvas


def main(keys):
    importlib.reload(glyphs)
    tiles = []
    for key, img, src, gbox, m in entries():
        if keys and key not in keys:
            continue
        tiles.append(tile(key, img, gbox, m, glyphs.GLYPHS.get(key), glyphs.PEN))
    per_row, per_sheet = 4, 8
    for si in range(0, len(tiles), per_sheet):
        group = tiles[si:si + per_sheet]
        rows = []
        for ri in range(0, len(group), per_row):
            row = group[ri:ri + per_row]
            h = max(t.shape[0] for t in row)
            row = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 8, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in row]
            rows.append(np.hstack(row))
        w = max(r.shape[1] for r in rows)
        rows = [cv2.copyMakeBorder(r, 0, 8, 0, w - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in rows]
        name = "sheet_%d.png" % (si // per_sheet) if not keys else "sel_%d.png" % (si // per_sheet)
        cv2.imwrite(os.path.join(OUT, name), np.vstack(rows))
    print("tiles:", len(tiles))


if __name__ == "__main__":
    main(set(sys.argv[1:]))

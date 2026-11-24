"""Turn stroke definitions into polylines (font units).

Stroke kinds (all coordinates in font units, y up, baseline = 0, cap height = 700):
  ("L", (x, y), (x, y), ...)              straight polyline
  ("Z", (x, y), (x, y), ...)              closed straight polygon outline
  ("E", (cx, cy), rx, ry[, rot])          full ellipse outline (rot in degrees, CCW)
  ("A", (cx, cy), rx, ry, a0, a1[, rot])  elliptical arc from angle a0 to a1 (degrees, CCW, 0 = +x)
  ("Q", p0, ctrl, p1)                     quadratic curve (for the few intentionally curved strokes)
  ("D", (x, y)[, r])                      filled dot (default radius = pen * 0.75)
"""
import math

SNAP_DEG = 5  # nearly horizontal/vertical lines are made exactly so


def snap_polyline(pts):
    pts = [list(p) for p in pts]
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0)) % 180
        if min(ang, 180 - ang) < SNAP_DEG:
            pts[i + 1][1] = y0
        elif abs(ang - 90) < SNAP_DEG:
            pts[i + 1][0] = x0
    return [tuple(p) for p in pts]


def arc_points(cx, cy, rx, ry, a0, a1, rot=0.0, step=6.0):
    n = max(8, int(abs(a1 - a0) / step))
    r = math.radians(rot)
    out = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)))
    return out


def expand(strokes, pen):
    """-> (polylines, closed_flags, dots[(x, y, r)])"""
    lines, closed, dots = [], [], []
    for s in strokes:
        kind, args = s[0], s[1:]
        if kind == "L":
            lines.append(snap_polyline(args)); closed.append(False)
        elif kind == "Z":
            lines.append(snap_polyline(list(args) + [args[0]])); closed.append(True)
        elif kind == "E":
            (cx, cy), rx, ry = args[:3]
            rot = args[3] if len(args) > 3 else 0
            lines.append(arc_points(cx, cy, rx, ry, 0, 360, rot)); closed.append(True)
        elif kind == "A":
            (cx, cy), rx, ry, a0, a1 = args[:5]
            rot = args[5] if len(args) > 5 else 0
            lines.append(arc_points(cx, cy, rx, ry, a0, a1, rot)); closed.append(False)
        elif kind == "Q":
            (x0, y0), (cx, cy), (x1, y1) = args
            n = 24
            pts = []
            for i in range(n + 1):
                t = i / n
                a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
                pts.append((a * x0 + b * cx + c * x1, a * y0 + b * cy + c * y1))
            lines.append(pts); closed.append(False)
        elif kind == "D":
            (x, y) = args[0]
            r = args[1] if len(args) > 1 else pen * 0.75
            dots.append((x, y, r))
        else:
            raise ValueError("unknown stroke kind %r" % kind)
    return lines, closed, dots


def bbox(strokes, pen):
    lines, _, dots = expand(strokes, pen)
    xs = [p[0] for l in lines for p in l] + [d[0] - d[2] for d in dots] + [d[0] + d[2] for d in dots]
    ys = [p[1] for l in lines for p in l] + [d[1] - d[2] for d in dots] + [d[1] + d[2] for d in dots]
    h = pen / 2
    return min(xs) - h, min(ys) - h, max(xs) + h, max(ys) + h

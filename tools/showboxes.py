import cv2, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from sources import ENTRIES, SCALE
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
imgs = {}
for key, img, src, g in ENTRIES:
    if img not in imgs:
        imgs[img] = cv2.imread(os.path.join(ROOT, "source", img + "_upright.png"))
    for b, c in ((src, (255, 0, 0)), (g, (0, 0, 255))):
        x0, y0, x1, y1 = [int(v * SCALE) for v in b]
        cv2.rectangle(imgs[img], (x0, y0), (x1, y1), c, 5)
    x0, y0 = int(g[0] * SCALE), int(g[1] * SCALE)
    cv2.putText(imgs[img], key, (x0, y0 - 8), 0, 1.5, (0, 0, 255), 3)
for n, im in imgs.items():
    cv2.imwrite(os.path.join(ROOT, "build", "grid", n + "_boxes.jpg"), cv2.resize(im, None, fx=0.5, fy=0.5))

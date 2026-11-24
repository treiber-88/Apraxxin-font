"""Rotate the source photos upright and write gridded previews for locating glyphs."""
import cv2, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = {"letters_1": None, "letters_2": cv2.ROTATE_90_CLOCKWISE,
       "numbers": cv2.ROTATE_90_CLOCKWISE, "punctuation": None}
os.makedirs(os.path.join(ROOT, "build", "grid"), exist_ok=True)
for name, rot in SRC.items():
    img = cv2.imread(os.path.join(ROOT, name + ".jpg"))
    if rot is not None:
        img = cv2.rotate(img, rot)
    cv2.imwrite(os.path.join(ROOT, "source", name + "_upright.png"), img)
    g = img.copy()
    h, w = g.shape[:2]
    for x in range(0, w, 100):
        cv2.line(g, (x, 0), (x, h), (0, 0, 255) if x % 500 == 0 else (200, 200, 255), 3 if x % 500 == 0 else 1)
        if x % 500 == 0: cv2.putText(g, str(x), (x + 5, 60), 0, 2, (0, 0, 255), 4)
    for y in range(0, h, 100):
        cv2.line(g, (0, y), (w, y), (255, 0, 0) if y % 500 == 0 else (255, 200, 200), 3 if y % 500 == 0 else 1)
        if y % 500 == 0: cv2.putText(g, str(y), (5, y - 5), 0, 2, (255, 0, 0), 4)
    cv2.imwrite(os.path.join(ROOT, "build", "grid", name + ".jpg"), g, [cv2.IMWRITE_JPEG_QUALITY, 80])
    print(name, w, h)

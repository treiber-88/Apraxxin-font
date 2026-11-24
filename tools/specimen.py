"""Render a specimen of build/Apraxxin.ttf next to a normal font -> build/specimen.png"""
import os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
font = os.path.join(ROOT, "build", "Apraxxin.ttf")
lines = ["abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789",
         ": ; , ' ` / \ + - = \u201c \u201d ! . ? & * \u2014 ( ) [ ] { }",
         "Hello, world! This is Apraxxin.", "The quick brown fox jumps over 12 lazy dogs?"]
W = 2400
img = Image.new("RGB", (W, 1500), "white")
d = ImageDraw.Draw(img)
ref = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 30)
y = 20
for size in (64, 28):
    f = ImageFont.truetype(font, size)
    for t in lines:
        d.text((20, y), t, font=ref, fill=(150, 150, 150))
        y += 40
        d.line((20, y + size * 0.8, W - 20, y + size * 0.8), fill=(200, 230, 255))
        d.text((20, y), t, font=f, fill="black")
        y += int(size * 1.45)
img = img.crop((0, 0, W, y + 10))
img.save(os.path.join(ROOT, "build", "specimen.png"))

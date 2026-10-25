from PIL import Image, ImageFilter, ImageChops, ImageDraw
import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
im = Image.open("assets/helmet_template.png").convert("RGBA")
W, H = im.size
px = im.load()
black = Image.new("L", (W, H), 0); white = Image.new("L", (W, H), 0)
bp, wp = black.load(), white.load()
for y in range(H):
    for x in range(W):
        r, g, b, a = px[x, y]
        if a > 128:
            (bp if r + g + b < 380 else wp)[x, y] = 255
# facemask zone (front/lower right), excluding the shell's own front edge
zone = Image.new("L", (W, H), 0)
ImageDraw.Draw(zone).polygon([(232, 300), (240, 255), (300, 205), (330, 172), (392, 118), (470, 112), (546, 270),
                              (546, 430), (370, 430), (300, 372), (240, 335)], fill=255)
core = black.filter(ImageFilter.MinFilter(29)).filter(ImageFilter.MaxFilter(37))   # only the big solid shell survives
mask = ImageChops.multiply(ImageChops.subtract(black, core), zone)
shell = ImageChops.subtract(black, mask)
shine = ImageChops.subtract(white, zone)            # highlight streak + ear hole; white inside the zone = gaps
sil = ImageChops.lighter(black, shine)
outline = ImageChops.subtract(sil.filter(ImageFilter.MaxFilter(5)), sil)
for n, m in (("shell", shell), ("mask", mask), ("shine", shine), ("outline", outline)):
    m.save(f"assets/helmet_{n}.png")

def colorize(shell_c, mask_c, shine_c, outline_c=(17, 24, 39, 255)):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for m, c in ((outline, outline_c), (shell, shell_c), (shine, shine_c), (mask, mask_c)):
        out.paste(Image.new("RGBA", (W, H), c), (0, 0), m)
    return out

if __name__ == "__main__":
    teams = [((227, 24, 55, 255), (154, 154, 154, 255), (255, 255, 255, 255)),
             ((255, 182, 18, 255), (32, 55, 49, 255), (255, 255, 255, 255)),
             ((0, 51, 141, 255), (0, 51, 141, 255), (198, 12, 48, 255))]
    prev = Image.new("RGBA", (W * 3 + 40, H + 20), (255, 251, 240, 255))
    for i, t in enumerate(teams):
        prev.alpha_composite(colorize(*t), (10 + i * (W + 10), 10))
    prev.convert("RGB").save("/private/tmp/claude-501/recolor_test.png"); print("ok")

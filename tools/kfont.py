import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
G7 = ImageFont.truetype(os.path.join(HERE, '..', 'work', 'fonts', 'Galmuri7.ttf'), 8)
ASCII = set(" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_")
def ascii_ok(c): return c in ASCII
def bitmap8(c):
    im = Image.new('L', (12, 12)); ImageDraw.Draw(im).text((0, -1), c, font=G7, fill=255)
    return [[1 if im.getpixel((x, y)) > 128 else 0 for x in range(8)] for y in range(8)]
def to4bpp(px):
    b = bytearray(32)
    for y in range(8):
        for x in range(8):
            v = px[y][x]
            for p in range(4):
                if v >> p & 1: b[(p // 2) * 16 + y * 2 + (p & 1)] |= 0x80 >> x
    return bytes(b)
def glyph8(c, body=15, shadow=12):
    m = bitmap8(c)
    px = [[0] * 8 for _ in range(8)]
    for y in range(8):
        for x in range(8):
            if m[y][x]: px[y][x] = body
            elif x > 0 and m[y][x - 1]: px[y][x] = shadow
    return to4bpp(px)

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kfont import to4bpp
def texts(): return []
def asm_code(): return ''
def lz_literal(data):
    out = bytearray([len(data) & 255, len(data) >> 8, 0, 0])
    for i in range(0, len(data), 8):
        ch = data[i:i + 8]; out.append(0xff); out += ch
    return bytes(out)
FREE = [0xB88000]
def store(put, data):
    a = FREE[0]; put(a, data)
    # advance in LoROM space
    o = ((a >> 16) & 0x7f) * 0x8000 + (a & 0x7fff) + len(data)
    FREE[0] = ((o // 0x8000) | 0x80) << 16 | (o % 0x8000) | 0x8000
    return a
def set_asset(put, idx, a):
    from_ = 0x8DDE33 + idx * 3
    put(from_, bytes([a & 255, (a >> 8) & 255, a >> 16]))
def prologue(put):
    import prologue as P
    pages = P.render('NanumSquareNeo-cBd.ttf', 11)
    uniq, maps = P.tiles_of(pages)
    assert len(uniq) <= 256, len(uniq)
    sheet = bytearray(8192)
    for t, i in uniq.items():
        px = [[15 if t[y * 8 + x] else 0 for x in range(8)] for y in range(8)]
        sheet[i * 32:i * 32 + 32] = to4bpp(px)
    blank = uniq[bytes(64)]
    mp = bytearray(8192)
    for q, m in enumerate(maps):
        for r in range(32):
            for c in range(32):
                o = q * 2048 + (r * 32 + c) * 2; mp[o] = blank & 255; mp[o + 1] = blank >> 8
        r0 = 11 if len(m) <= 6 else 10
        for r, row in enumerate(m):
            for c, t in enumerate(row):
                o = q * 2048 + ((r0 + r) * 32 + c) * 2; mp[o] = t & 255; mp[o + 1] = t >> 8
    set_asset(put, 86, store(put, lz_literal(bytes(sheet))))
    set_asset(put, 81, store(put, lz_literal(bytes(mp))))
def apply(rom, put, expect, off, L):
    prologue(put)
    mtitle(rom, put)
    title(rom, put)
    options(rom, put)
    result(rom, put)
    ranking(rom, put)
    continue_(rom, put)
    pause(rom, put)
    briefing(rom, put)
    yesno(rom, put)
    store_a14(put)
    set_asset(put, 2, store(put, lz_literal(bytes(F2[0]))))

MT = {24: "서장  길모어 연구소편", 25: "잠입  비밀기지편", 26: "빙해의 격투  북극해편",
      27: "하늘의 위협  부유요새편", 28: "결전  본거지 병기공장편"}
MT_SLOTS = [0x2a, 0x2c, 0x2e] + [k + 2 * j for k in (0x40, 0x60, 0x80, 0xa0) for j in range(8)] + [0xc0, 0xc2, 0xc4]
def glyph16(ch, font='SeoulHangangEB.ttf', size=16, thr=70):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'fonts', font), 'rb'), size)
    im = Image.new('L', (16, 16)); d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), ch, font=f)
    d.text(((16 - (bb[2] - bb[0])) // 2 - bb[0], (16 - (bb[3] - bb[1])) // 2 - bb[1]), ch, font=f, fill=255)
    return [[1 if im.getpixel((x, y)) > thr else 0 for x in range(16)] for y in range(16)]
def mtitle(rom, put):
    import lzss
    tab = lzss.table(rom)
    sheet = bytearray(lzss.decomp(rom, lzss.lo2pc(tab[5]))[0])
    chars = []
    for s in MT.values():
        for c in s:
            if c != ' ' and c not in chars: chars.append(c)
    assert len(chars) <= len(MT_SLOTS), len(chars)
    slot = {}
    for c, k in zip(chars, MT_SLOTS):
        slot[c] = k; g = glyph16(c)
        for q, (ox, oy) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
            px = [[6 if g[oy + y][ox + x] else 0 for x in range(8)] for y in range(8)]
            t = k + (q & 1) + (q >> 1) * 16
            sheet[t * 32:t * 32 + 32] = to4bpp(px)
    # big "MISSION" -> 미션 / 최종 미션 (cells e0..e6)
    big = {}
    for ch, k in (('미', 0xe0), ('션', 0xe2), ('최', 0xe4), ('종', 0xe6)):
        m = _mask(_render(ch, 'SeoulHangangEB.ttf', 60, 64, 32), 16, 16, 14, 13, 1, 110)
        px = [[0] * 16 for _ in range(16)]
        for y in range(16):
            for x in range(16):
                if m[y][x]:
                    px[y][x] = 2 if (x == 0 or not m[y][x - 1]) else (1 if y <= 6 else 5 if y <= 9 else 4 if y <= 11 else 3)
        for q, (ox, oy) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
            t = k + (q & 1) + (q >> 1) * 16
            sheet[t * 32:t * 32 + 32] = to4bpp([px[oy + y][ox:ox + 8] for y in range(8)])
        big[ch] = k
    # TEAM LEADER -> 팀 리더 (tiles 04-09 / 0a-0f,20)
    for text, tiles, w in (('팀', list(range(4, 10)), 16), ('리더', list(range(10, 16)) + [0x20, 0x21], 34)):
        W = len(tiles) * 8
        m = _mask(_render(text, 'SeoulHangangEB.ttf', 60, 64, 32), W, 16, w, 12, 1, 100)
        m = [[0] * 9 + row[:W - 9] for row in m] if text == '리더' else m
        for i, t in enumerate(tiles):
            for half in (0, 1):
                px = [[7 if m[half * 8 + y][i * 8 + x] else 0 for x in range(8)] for y in range(8)]
                _tile_put(sheet, t + half * 16, px)
    set_asset(put, 5, store(put, lz_literal(bytes(sheet))))
    for a_, v in ((0x99E426, 0x1112), (0x99E49C, 0x1912), (0x99E43A, 0x1132), (0x99E4B0, 0x1932)):
        put(a_, bytes([v & 255, v >> 8]))
    for idx, s in MT.items():
        mp = bytearray(lzss.decomp(rom, lzss.lo2pc(tab[idx]))[0])
        for r in (12, 13):
            for c in range(32): mp[(r * 32 + c) * 2:(r * 32 + c) * 2 + 2] = b'\0\0'
        w = sum(1 if c == ' ' else 2 for c in s); x = (32 - w) // 2
        for c in s:
            if c == ' ': x += 1; continue
            k = slot[c]
            for q in range(4):
                o = ((12 + (q >> 1)) * 32 + x + (q & 1)) * 2
                mp[o] = k + (q & 1) + (q >> 1) * 16; mp[o + 1] = 0
            x += 2
        hi = mp[(8 * 32 + 7) * 2 + 1] if idx < 28 else mp[(8 * 32 + 15) * 2 + 1]
        dig = [mp[(8 * 32 + 23) * 2]] if idx < 28 else []
        for r in (8, 9):
            for c in range(32): mp[(r * 32 + c) * 2:(r * 32 + c) * 2 + 2] = b'\0\0'
        def put16(col, k):
            for q in range(4):
                o = ((8 + (q >> 1)) * 32 + col + (q & 1)) * 2
                mp[o] = k + (q & 1) + (q >> 1) * 16; mp[o + 1] = hi
        if idx < 28:
            put16(12, big['미']); put16(14, big['션'])
        else:
            put16(11, big['최']); put16(13, big['종']); put16(16, big['미']); put16(18, big['션'])
        set_asset(put, idx, store(put, lz_literal(bytes(mp))))

def _font(name, size):
    from PIL import ImageFont
    return ImageFont.truetype(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'fonts', name), 'rb'), size)
def _tile_put(sheet, k, px):
    sheet[k * 32:k * 32 + 32] = to4bpp(px)
def _block(sheet, col, row, img, colormap, w=None, h=None):
    """write PIL L image into tile grid (16 tiles per row) at tile col,row"""
    w = w or img.width; h = h or img.height
    for ty in range(h // 8):
        for tx in range(w // 8):
            px = [[colormap(img.getpixel((tx * 8 + x, ty * 8 + y))) for x in range(8)] for y in range(8)]
            _tile_put(sheet, (row + ty) * 16 + col + tx, px)
def title(rom, put):
    import lzss
    from PIL import Image, ImageDraw
    tab = lzss.table(rom)
    sh = bytearray(lzss.decomp(rom, lzss.lo2pc(tab[55]))[0])
    # menu words: 16x16 sprites
    f = _font('NanumSquareNeo-eHv.ttf', 15)
    def word(cells, text):
        im = Image.new('L', (16 * len(cells), 16)); d = ImageDraw.Draw(im)
        x = 0
        for ch in text:
            bb = d.textbbox((0, 0), ch, font=f)
            d.text((x + (16 - (bb[2] - bb[0])) // 2 - bb[0], (16 - (bb[3] - bb[1])) // 2 - bb[1]), ch, font=f, fill=255)
            x += 16
        for i, (c, r) in enumerate(cells):
            _block(sh, c, r, im.crop((i * 16, 0, i * 16 + 16, 16)), lambda v: 15 if v > 110 else 0)
    word([(12, 0), (14, 0)], '게임')
    word([(12, 2), (14, 2), (10, 4)], '시작')
    word([(12, 4), (14, 4), (10, 6)], '설정')
    # logo 80x32 at tiles (0,4)
    big = _font('NanumSquareNeo-eHv.ttf', 64)
    im = Image.new('L', (400, 100)); d = ImageDraw.Draw(im)
    d.text((10, 0), '사이보그', font=big, fill=255)
    im = im.crop(im.getbbox())
    im = im.resize((70, 26), Image.LANCZOS)
    im = im.transform((80, 32), Image.AFFINE, (1, 0.25, -3, 0, 1, -3), Image.BICUBIC)
    def cm(v):
        if v > 170: return 4
        if v > 110: return 5
        if v > 60: return 6
        if v > 25: return 7
        return 0
    _block(sh, 0, 4, im, cm, 80, 32)
    set_asset(put, 55, store(put, lz_literal(bytes(sh))))

OPT_MAIN = {3: None, 5: '사운드 테스트', 7: '음성 출력', 11: '밝기', 13: '나가기'}
OPT_DIFF = ['  쉬움  ', '  보통  ', ' 어려움  ']
def options(rom, put):
    import lzss
    from kfont import glyph8
    tab = lzss.table(rom)
    texts = list(OPT_MAIN.values()) + OPT_DIFF + ['설정', '조작 타입', '배경음', '효과음', '스테레오', '모노', '타입',
             '특수1', '특수2', '광선', '점프', '어둠', '밝음', '컨티뉴']
    chars = []
    for s in texts:
        for c in s or '':
            if c != ' ' and not c.isascii() and c not in chars: chars.append(c)
    assert len(chars) <= 48, len(chars)
    code = {c: 0x60 + i for i, c in enumerate(chars)}
    team = []
    for c in '능력치공격방어속도차지':
        if c not in team: team.append(c)
    tslots = [0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x3B, 0x3C, 0x3E, 0x40]
    for c, k in zip(team, tslots): code[c] = k
    f2 = bytearray(lzss.decomp(rom, lzss.lo2pc(tab[2]))[0])
    for c, k in code.items(): f2[k * 32:k * 32 + 32] = glyph8(c)
    F2[0] = f2; CODE.update(code)
    def words(s, hi=0x1e):
        out = []
        for c in s:
            if c == ' ': out.append(0)
            else: out.append((code[c] if c in code else ord(c)) | hi << 8)
        return out
    # main window (asset 3)
    m3 = bytearray(lzss.decomp(rom, lzss.lo2pc(tab[3]))[0])
    def wrow(buf, base, row, col0, cols, s, stride=32):
        ws = words(s)
        for c in range(cols):
            v = ws[c] if c < len(ws) else 0
            o = base + (row * stride + col0 + c) * 2; buf[o] = v & 255; buf[o + 1] = v >> 8
    wrow(m3, 0, 1, 13, 6, '  설정')
    for row, s in OPT_MAIN.items():
        if s: wrow(m3, 0, row, 8, 16, ' ' * ((16 - len(s)) // 2) + s)
    wrow(m3, 0, 9, 8, 12, '      조작 타입')   # col 20 = type letter (code-written)
    m3[(9 * 32 + 20) * 2:(9 * 32 + 20) * 2 + 2] = bytes([0x41, 0x1e])
    set_asset(put, 3, store(put, lz_literal(bytes(m3))))
    # difficulty label $19:A090 (3 x 6 words)
    dw = [w for s in OPT_DIFF for w in words(s)]; assert len(dw) == 18
    put(0x99A090, b''.join(bytes([w & 255, w >> 8]) for w in dw))
    # sub windows $8D:A000
    sub = bytearray(rom[0x6a000:0x6ad00])
    offs = [sub[i * 2] | sub[i * 2 + 1] << 8 for i in range(17)]
    def srow(i, row, col0, n, s, keep=()):
        o = offs[i]; ws = words(s)
        for c in range(n):
            if col0 + c in keep: continue
            v = ws[c] if c < len(ws) else 0
            p = o + (row * 14 + col0 + c) * 2; sub[p] = v & 255; sub[p + 1] = v >> 8
    for i in (1, 2):
        srow(i, 2, 3, 4, ' 배경음'); srow(i, 4, 3, 4, ' 효과음')
    srow(3, 3, 0, 14, '  스테레오  모노')
    names = {'SP1': '특수1', 'SP2': '특수2', 'RAY': '광선', 'JUMP': '점프'}
    for i in range(4, 10):
        o = offs[i]
        L = chr(0x41 + i - 4)
        srow(i, 0, 0, 6, '타입 ' + L)
        for row, col in ((1, 7), (3, 4), (3, 10), (5, 7)):
            # read original label
            lab = ''
            for c in range(col, 14):
                v = sub[o + (row * 14 + c) * 2]
                if v == 0: break
                lab += chr(v)
            srow(i, row, col, len(lab), names[lab])
    for i in range(10, 14):
        srow(i, 3, 1, 2, '어둠'); srow(i, 3, 11, 2, '밝음')
    for i, (d, n) in zip((14, 15, 16), (('쉬움', 5), ('보통', 3), ('어려움', 1))):
        srow(i, 2, 0, 14, ' ' * ((14 - len(d)) // 2) + d)
        srow(i, 4, 0, 14, '    컨티뉴 ' + str(n))
    put(0x8DA000, bytes(sub))
    # team select status labels ($19:91C8..)
    def imm(a, ws):
        for i, w in enumerate(ws): put(a + i * 6, bytes([w & 255, w >> 8]))
    sp = 0x1e20
    imm(0x9991C9, [sp] + words('능력치') + [sp, sp])
    imm(0x9991F3, words('공격')); imm(0x999205, words('방어')); imm(0x999217, words('속도')); imm(0x999229, words('차지'))

F2 = [None]; CODE = {}
BIG_CELLS = {}
def big16(ch):
    """16x16 gradient glyph (asset 14 style) -> 4 tiles px lists"""
    from PIL import Image, ImageDraw
    f = _font('NanumSquareNeo-eHv.ttf', 14)
    im = Image.new('L', (16, 16)); d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), ch, font=f)
    d.text(((15 - (bb[2] - bb[0])) // 2 - bb[0], (16 - (bb[3] - bb[1])) // 2 - bb[1]), ch, font=f, fill=255)
    m0 = [[1 if 1 <= x <= 14 and 1 <= y <= 14 and im.getpixel((x, y)) > 100 else 0 for x in range(16)] for y in range(16)]
    m = [[1 if m0[y][x] or (x > 1 and m0[y][x - 1]) else 0 for x in range(16)] for y in range(16)]
    def fill(x, y):
        k = (x + y) & 1
        return {1: 0xd, 2: 0x4, 3: (0x4, 0xf)[k], 4: (0xf, 0x4)[k], 5: 0xf, 6: 0xf, 7: 0xf, 8: 0x5, 9: 0x7, 10: 0x7,
                11: (0x9, 0x7)[k], 12: (0x7, 0x9)[k], 13: 0x9, 14: (0x8, 0x9)[k]}.get(y, 0x9)
    px = [[0] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            if m[y][x]: px[y][x] = fill(x, y)
            elif any(0 <= y + dy < 16 and 0 <= x + dx < 16 and m[y + dy][x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                px[y][x] = 0xe
    return [[row[ox:ox + 8] for row in px[oy:oy + 8]] for oy, ox in ((0, 0), (0, 8), (8, 0), (8, 8))]
def big_code(ch):
    """allocate 16x16 cell in #02 kana area 0xA0-0xDF; returns top-left code"""
    if ch not in BIG_CELLS:
        i = len(BIG_CELLS); assert i < 16
        c = 0x90 + (i % 8) * 2 + (i // 8) * 32
        for q, t in enumerate(big16(ch)):
            F2[0][(c + (q & 1) + (q >> 1) * 16) * 32:(c + (q & 1) + (q >> 1) * 16) * 32 + 32] = to4bpp(t)
        BIG_CELLS[ch] = c
    return BIG_CELLS[ch]
def result(rom, put):
    import lzss
    tab = lzss.table(rom)
    m = bytearray(lzss.decomp(rom, lzss.lo2pc(tab[16]))[0])
    def W(q, r, c): o = q * 2048 + (r * 32 + c) * 2; return m[o] | m[o + 1] << 8
    def S(q, r, c, v): o = q * 2048 + (r * 32 + c) * 2; m[o] = v & 255; m[o + 1] = v >> 8
    for q in range(2):
        hi = W(q, 12, 5) & 0xfc00
        def big(r, c0, text, clear=None):
            if clear:
                for c in range(clear[0], clear[1]):
                    S(q, r, c, 0); S(q, r + 1, c, 0)
            c = c0
            for ch in text:
                if ch != ' ':
                    k = 0x100 + big_code(ch)
                    S(q, r, c, hi | k); S(q, r, c + 1, hi | (k + 1)); S(q, r + 1, c, hi | (k + 16)); S(q, r + 1, c + 1, hi | (k + 17))
                c += 2
        big(2, 12, '미션', (0, 32))
        big(5, 13, '클리어', (0, 32))
        big(12, 11, '격파', (0, 15))
        big(15, 8, '시간', (0, 12))
        big(19, 10, '점수', (0, 14))
        # small text row 25 (#02 font, tile 0x100+code)
        for r in range(24, 28):
            row = [W(q, r, c) for c in range(32)]
            s = ''.join(chr(x & 0xff) if x and (x & 0x300) == 0x100 else ' ' for x in row)
            if 'CONTINUE' in s:
                i = s.index('CONTINUE'); h = row[i] & 0xfc00
                for j in range(8): S(q, r, i + j, 0)
                for j, ch in enumerate('컨티뉴'): S(q, r, i + 5 + j, h | 0x100 | CODE[ch])
    set_asset(put, 16, store(put, lz_literal(bytes(m))))
    # mission digit position (row 2 col 18)
    for a, v in ((0x99B756, 0x1052), (0x99B763, 0x1072), (0x99B774, 0x1452), (0x99B785, 0x1472)):
        put(a, bytes([v & 255, v >> 8]))

A14 = [None]
def _a14(rom):
    import lzss
    if A14[0] is None: A14[0] = bytearray(lzss.decomp(rom, lzss.lo2pc(lzss.table(rom)[14]))[0])
    return A14[0]
def _render(text, font, size, W, H, dil=1, thr=100):
    from PIL import Image, ImageDraw
    f = _font(font, size)
    im = Image.new('L', (W * 4, H * 4)); d = ImageDraw.Draw(im)
    d.text((4, 4), text, font=f, fill=255)
    bb = im.getbbox(); im = im.crop(bb)
    return im
def _mask(im, W, H, w, h, dil=1, thr=100):
    from PIL import Image
    im = im.resize((w, h), Image.LANCZOS)
    c = Image.new('L', (W, H)); c.paste(im, ((W - w) // 2, (H - h) // 2))
    m0 = [[1 if c.getpixel((x, y)) > thr else 0 for x in range(W)] for y in range(H)]
    m = [[1 if m0[y][x] or (dil and x > 0 and m0[y][x - 1]) else 0 for x in range(W)] for y in range(H)]
    return m
def _outline(m, x, y):
    H = len(m); W = len(m[0])
    return any(0 <= y + dy < H and 0 <= x + dx < W and m[y + dy][x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1))
def ranking(rom, put):
    import lzss
    a = _a14(rom)
    def tput(t, px): a[t * 32:t * 32 + 32] = to4bpp(px)
    # big RANKING (256x24) -> 랭킹
    F = [0, 6, 3, 5, (7, 5), 7, 2, 2, 1, 1, 15, (2, 15), 4, 4, 8, 3, 3, 5, 5, 7, 2, 4, 6, 5]
    m = _mask(_render('랭킹', 'NanumSquareNeo-eHv.ttf', 60, 256, 24), 256, 24, 64, 22)
    img = [[0] * 256 for _ in range(24)]
    for y in range(24):
        for x in range(256):
            if m[y][x]:
                v = F[y]; img[y][x] = v[(x + y) & 1] if isinstance(v, tuple) else v
            elif _outline(m, x, y): img[y][x] = 6
    for r_ in range(3):
        for c in range(32):
            t = (0x100 + c if c < 16 else 0x140 + c - 16) + 0x10 * r_
            tput(t, [img[r_ * 8 + y][c * 8:c * 8 + 8] for y in range(8)])
    # header pieces (8x16)
    slots = [0xa7, 0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xae, 0xaf, 0xc8, 0xc9, 0xea, 0xeb, 0xec, 0xed, 0xee, 0xef]
    piece = {}
    def glyph(ch):
        if ch in piece: return piece[ch]
        mm = _mask(_render(ch, 'NanumSquareNeo-dEb.ttf', 40, 16, 16), 16, 16, 14, 13, 1, 120)
        px = [[8 if mm[y][x] else (0xe if (x > 0 and y > 0 and mm[y - 1][x - 1]) else 0) for x in range(16)] for y in range(16)]
        L, R = slots.pop(0), slots.pop(0)
        for t, ox in ((L, 0), (R, 8)):
            tput(t, [px[y][ox:ox + 8] for y in range(8)]); tput(t + 16, [px[y][ox:ox + 8] for y in range(8, 16)])
        piece[ch] = (L, R); return piece[ch]
    m15 = bytearray(lzss.decomp(rom, lzss.lo2pc(lzss.table(rom)[15]))[0])
    for q in (0, 2):
        o0 = q * 2048
        hi = (m15[o0 + (6 * 32 + 2) * 2 + 1] << 8) & 0xfc00
        for c in range(32):
            for r_ in (6, 7):
                o = o0 + (r_ * 32 + c) * 2; m15[o] = m15[o + 1] = 0
        for col, txt in ((1, '순위'), (9, '점수'), (19, '이름'), (25, '미션')):
            for ch in txt:
                L, R = glyph(ch)
                for dc, t in ((0, L), (1, R)):
                    for dr in (0, 1):
                        o = o0 + ((6 + dr) * 32 + col + dc) * 2; v = hi | (t + 16 * dr)
                        m15[o] = v & 255; m15[o + 1] = v >> 8
                col += 2
    set_asset(put, 15, store(put, lz_literal(bytes(m15))))
def store_a14(put):
    if A14[0] is not None: set_asset(put, 14, store(put, lz_literal(bytes(A14[0]))))

METAL = [0, 6, 3, 5, (7, 5), 7, 2, 2, 1, 1, 15, (2, 15), 4, 4, 8, 3, 3, 5, 5, 7, 2, 4, 6, 5]
def _metal_img(m):
    W = len(m[0]); img = [[0] * W for _ in range(24)]
    for y in range(24):
        for x in range(W):
            if m[y][x]:
                v = METAL[y]; img[y][x] = v[(x + y) & 1] if isinstance(v, tuple) else v
            elif _outline(m, x, y): img[y][x] = 6
    return img
def _px_of(a, t):
    b = a[t * 32:t * 32 + 32]
    return [[((b[y*2]>>(7-x))&1)|((b[y*2+1]>>(7-x))&1)<<1|((b[16+y*2]>>(7-x))&1)<<2|((b[17+y*2]>>(7-x))&1)<<3 for x in range(8)] for y in range(8)]
def continue_(rom, put):
    import lzss
    a = bytearray(lzss.decomp(rom, lzss.lo2pc(lzss.table(rom)[10]))[0])
    def tput(t, px): a[t * 32:t * 32 + 32] = to4bpp(px)
    m = _mask(_render('컨티뉴 ?', 'NanumSquareNeo-eHv.ttf', 60, 256, 24), 256, 24, 120, 22)
    img = _metal_img(m)
    for r_ in range(3):
        for c in range(32):
            t = (c if c < 16 else 0x40 + c - 16) + 0x10 * r_
            tput(t, [img[r_ * 8 + y][c * 8:c * 8 + 8] for y in range(8)])
    for base, txt, w in ((0x80, '예', 16), (0xc0, '아니오', 42)):
        # read original box
        box = [[0] * 48 for _ in range(24)]
        for r_ in range(3):
            for c in range(6):
                p = _px_of(a, base + r_ * 16 + c)
                for y in range(8): box[r_ * 8 + y][c * 8:c * 8 + 8] = p[y]
        for y in range(1, 22):
            for x in range(1, 47): box[y][x] = 0xd
        mm = _mask(_render(txt, 'NanumSquareNeo-eHv.ttf', 60, 48, 24), 46, 20, w, 16)
        for y in range(20):
            for x in range(46):
                X, Y = x + 1, y + 2
                if mm[y][x]:
                    up = y > 0 and mm[y - 1][x]; lf = x > 0 and mm[y][x - 1]
                    dn = y < 19 and mm[y + 1][x]; rt = x < 45 and mm[y][x + 1]
                    box[Y][X] = 0x9 if not (up and lf) else (0xc if not (dn and rt) else 0xb)
                elif _outline(mm, x, y): box[Y][X] = 0xf
        for r_ in range(3):
            for c in range(6):
                tput(base + r_ * 16 + c, [box[r_ * 8 + y][c * 8:c * 8 + 8] for y in range(8)])
    set_asset(put, 10, store(put, lz_literal(bytes(a))))

A18_TXT = {0: '미션', 1: '최종 미션', 2: '일본', 3: '영국', 4: '북극해', 5: '그리스', 6: '독일'}
def briefing(rom, put):
    import lzss
    a = bytearray(lzss.decomp(rom, lzss.lo2pc(lzss.table(rom)[18]))[0])
    def strip(row):
        img = [[0] * 128 for _ in range(16)]
        for c in range(16):
            for h in range(2):
                p = _px_of(a, row * 32 + h * 16 + c)
                for y in range(8): img[h * 8 + y][c * 8:c * 8 + 8] = p[y]
        return img
    def unstrip(row, img):
        for c in range(16):
            for h in range(2):
                t = row * 32 + h * 16 + c
                a[t * 32:t * 32 + 32] = to4bpp([img[h * 8 + y][c * 8:c * 8 + 8] for y in range(8)])
    def draw(img, x0, x1, text, style):
        from PIL import Image, ImageDraw, ImageFont
        for y in range(16):
            for x in range(x0, x1): img[y][x] = 0
        f = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'fonts', 'Galmuri9.ttf'), 10)
        im = Image.new('L', (128, 16)); d = ImageDraw.Draw(im)
        w = d.textlength(text, font=f)
        d.text((x1 - w - 1 if style == 'm' else x0 + ((x1 - x0) - w) // 2, 0), text, font=f, fill=255)
        m = [[1 if im.getpixel((x, y)) > 128 else 0 for x in range(128)] for y in range(16)]
        m = [[1 if m[y][x] or (x > 0 and m[y][x - 1]) else 0 for x in range(128)] for y in range(16)]
        for y in range(16):
            for x in range(x0, x1):
                if m[y][x]:
                    edge = not m[y][x - 1]
                    if style == 'w': v = 1 if edge else 0xf
                    else: v = 2 if edge else (1 if y <= 3 else 5 if y <= 6 else 4 if y <= 8 else 3)
                    img[y][x] = v
    for row, txt in A18_TXT.items():
        img = strip(row)
        cols = [x for x in range(128) if any(img[y][x] for y in range(16))]
        x0, x1 = min(cols), max(cols) + 1
        if row >= 2: x0, x1 = 0, 128
        if row == 1:
            draw(img, 0, 50, '최종', 'c'); draw(img, 52, 128, '미션', 'c')
        else:
            draw(img, x0, x1, txt, 'w' if row >= 2 else 'm')
        unstrip(row, img)
    img = strip(7)
    cols = [x for x in range(65, 128) if any(img[y][x] for y in range(16))]
    draw(img, min(cols), max(cols) + 1, '시작', 'm')
    unstrip(7, img)
    set_asset(put, 18, store(put, lz_literal(bytes(a))))

def yesno(rom, put):
    import lzss
    from kfont import bitmap8
    a = bytearray(lzss.decomp(rom, lzss.lo2pc(lzss.table(rom)[35]))[0])
    for t0, txt, body, sh in ((0x36, '예', 8, 7), (0x38, '아니', 8, 7), (0x3a, '예', 5, 0xb), (0x3c, '아니', 5, 0xb)):
        img = [[0] * 16 for _ in range(8)]
        x = (16 - 8 * len(txt)) // 2
        for ch in txt:
            m = bitmap8(ch)
            for y in range(8):
                for xx in range(8):
                    if m[y][xx]: img[y][x + xx] = body
            x += 8
        for i in range(2):
            t = t0 + i
            a[t * 32:t * 32 + 32] = to4bpp([img[y][i * 8:i * 8 + 8] for y in range(8)])
    set_asset(put, 35, store(put, lz_literal(bytes(a))))

def pause(rom, put):
    # sprite font: ROM pc 0x903E0 + code*32 ; "X0 PAUSE" string at pc 0xB17C
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'fonts', 'Galmuri7.ttf'), 8)
    for i, ch in enumerate('일시정지'):
        im = Image.new('L', (8, 8)); d = ImageDraw.Draw(im)
        bb = d.textbbox((0, 0), ch, font=f)
        d.text(((8 - (bb[2] - bb[0])) // 2 - bb[0], (8 - (bb[3] - bb[1])) // 2 - bb[1]), ch, font=f, fill=255)
        px = [[2 if im.getpixel((x, y)) > 100 else 0 for x in range(8)] for y in range(8)]
        pc = 0x903E0 + (0x5B + i) * 32
        put(0x800000 | ((pc >> 15) << 16) | 0x8000 | (pc & 0x7fff), to4bpp(px))
    pc = 0xB189 + 3
    put(0x800000 | ((pc >> 15) << 16) | 0x8000 | (pc & 0x7fff), bytes([0x5B, 0x5C, 0x5D, 0x5E, 0x20]))

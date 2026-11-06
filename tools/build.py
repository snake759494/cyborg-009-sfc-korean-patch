"""Cyborg 009 (SFC) Korean patch builder.
usage: python tools/build.py <orig.sfc> <out.sfc>"""
import sys, os, re, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a65 import asm
from kfont import glyph8, ascii_ok
import extras

ORIG_SHA = None
src, dst = sys.argv[1], sys.argv[2]
R = bytearray(open(src, 'rb').read())
ORIG_SHA = '71e77fdbd9c865ae07e907549b02549ebe87fa8d436401c485e588c61797754a'
if hashlib.sha256(R).hexdigest() != ORIG_SHA: sys.exit('원본 ROM SHA-256 불일치')
assert len(R) == 0x100000
rom = bytearray(R) + bytearray(b'\xff' * 0x100000)


def off(a):  # snes LoROM -> file offset
    return ((a >> 16) & 0x7f) * 0x8000 + (a & 0x7fff)


def put(a, b):
    o = off(a); rom[o:o + len(b)] = b


def expect(a, hexs):
    o = off(a); b = bytes.fromhex(hexs)
    assert rom[o:o + len(b)] == b, (hex(a), rom[o:o + len(b)].hex(), hexs)


# ---------------- script parsing ----------------
def parse_script(path):
    ents = {}; cur = None
    for line in open(path, encoding='utf8').read().split('\n'):
        if line.startswith('## '):
            cur = line[3:].strip(); ents[cur] = []; continue
        if cur is not None: ents[cur].append(line)
    out = {}
    for k, ls in ents.items():
        t = '\n'.join(ls)
        assert t.rstrip().endswith('[FA]'), k
        t = t.rstrip()
        out[k] = t
    return out


SCRIPT = parse_script(os.path.join(os.path.dirname(__file__), '..', 'translation', 'script_ko.txt'))
EXTRA_TEXT = extras.texts()   # other strings that need glyphs (none in dynamic font)

# glyph table
syl = []
def collect(t):
    for c in t:
        if '가' <= c <= '힣' and c not in syl: syl.append(c)
for t in SCRIPT.values(): collect(t)
syl.sort()
syl += [c for c in ',.!?' ]
GID = {c: i for i, c in enumerate(syl)}
assert len(syl) <= 190 * 8
print('hangul syllables:', len(syl))


def enc(t, width, lines_max, key):
    b = bytearray(); i = 0; col = 0; ln = 0; warn = []
    while i < len(t):
        c = t[i]
        if c == '[':
            j = t.index(']', i); b.append(int(t[i + 1:j], 16))
            code = int(t[i + 1:j], 16)
            if code == 0xFE: ln = 0
            i = j + 1; continue
        if c == '{':
            j = t.index('}', i); b.append(0xE0 + int(t[i + 1:j])); col += 1; i = j + 1; continue
        if c == '\n':
            b.append(0xFF); ln += 1; col = 0
            if ln >= lines_max and not t[i + 1:].startswith('[F'): warn.append(f'{key}: too many lines')
            i += 1; continue
        if c in GID:
            n = GID[c]; b += bytes([1 + n // 190, 0x20 + n % 190]); col += 1
        else:
            assert ascii_ok(c), (key, c)
            b.append(ord(c)); col += 1
        if col > width: warn.append(f'{key}: line too long: {t[:i+1].split(chr(10))[-1]}')
        i += 1
    for w in warn: print('WARN', w)
    return bytes(b)


# ---------------- ROM expansion / header ----------------
rom[0x7fd7] = 0x0b
# ---------------- glyph banks ----------------
for c, n in GID.items():
    o = 0x110000 + (n // 190) * 0x8000 + (n % 190) * 32
    rom[o:o + 32] = glyph8(c)

# ---------------- D-bank text -> $A0:8000 ----------------
dkeys = [k for k in SCRIPT if k.startswith('D.')]
pos = 0xA08000; addr = {}
for k in dkeys:
    lim = (12, 5)
    b = enc(SCRIPT[k], *lim, k)
    addr[k] = pos; put(pos, b); pos += len(b)
assert pos < 0xA10000
print('D text bytes', pos - 0xA08000)
rel = lambda a: (a - 0xC000) & 0xffff
w16 = lambda a, v: put(a, bytes([v & 255, v >> 8]))
for i in range(6): w16(0x8DC6FA + i * 2, rel(addr[f'D.intro{i}'] & 0xffff))
for i in range(8): w16(0x8DD186 + i * 2, rel(addr[f'D.prof{i}'] & 0xffff))
for i in range(8): w16(0x8DD317 + i * 2, rel(addr[f'D.call{i}'] & 0xffff))
for a, k in ((0x99978F, 'D.sel_2'), (0x999794, 'D.sel_1'), (0x99986A, 'D.sel_go'), (0x999956, 'D.sel_ok')):
    expect(a - 1, 'a9'); w16(a, rel(addr[k] & 0xffff))
# bank byte of $8D text readers -> $A0
for a in (0x9984DB, 0x9985B3, 0x999513, 0x999662, 0x99972A, 0x9997C6, 0x9998B2, 0x999988):
    expect(a, 'bf00008d'); put(a + 3, b'\xa0')

# ---------------- E-bank text -> $A1:D000 ----------------
E = bytearray()
hdr = 6
E += bytes(6)
g0 = len(E); E += bytes(10)
subs = []
for g in range(5):
    subs.append(len(E)); E += bytes(16)
g1 = len(E); E += bytes(16)
g2 = len(E); E += bytes(8)
def sw(o, v): E[o] = v & 255; E[o + 1] = v >> 8
sw(0, g0); sw(2, g1); sw(4, g2)
for g in range(5): sw(g0 + g * 2, subs[g])
eaddr = {}
def etext(k):
    if k not in eaddr:
        eaddr[k] = len(E); E.extend(enc(SCRIPT[k], 18, 4, k))
    return eaddr[k]
for g in range(5):
    for m in range(8):
        k = f'E.m{g}c{m}' if f'E.m{g}c{m}' in SCRIPT else 'E.m4c0'
        sw(subs[g] + m * 2, etext(k))
g1map = {0: 'E.g1c0', 1: 'E.g1c1', 2: 'E.g1c0', 3: 'E.g1c0', 4: 'E.g1c4', 5: 'E.g1c0', 6: 'E.g1c0', 7: 'E.g1c0'}
for m in range(8): sw(g1 + m * 2, etext(g1map[m]))
for g in range(4): sw(g2 + g * 2, etext(f'E.g2m{g}'))
assert 0xD000 + len(E) <= 0x10000
put(0xA1D000, bytes(E))
print('E text bytes', len(E))
# patch $91D000 references -> $A1D000
o = off(0x99D600); seg = rom[o:o + 0x400]
n = 0
for m in re.finditer(rb'\x00\xd0\x91', bytes(seg)):
    rom[o + m.start() + 2] = 0xa1; n += 1
print('E refs patched', n)

# ---------------- hook code at $BF:8000 ----------------
FB, RING, TMP = 0x7E1E00, 0x7E1E02, 0x7E1E04
code = f'''
fonthook:
 php
 rep.b #$30
 cmp.w #$0002
 bne fh1
 pha
 txa
 sta.l ${FB:06X}
 pla
fh1:
 jml $99F4A8

; upload glyph TMP(lead) TMP+1(second) -> returns A(8)=tile code, B preserved
kup:
 php
 phx
 phy
 xba
 pha
 rep.b #$30
 lda.l ${RING:06X}
 cmp.w #$0060
 bcc kupr0
 lda.w #$0000
kupr0:
 tax
 inc a
 cmp.w #$0060
 bcc kupr1
 lda.w #$0000
kupr1:
 sta.l ${RING:06X}
 txa
 clc
 adc.w #$0060
 sta.l ${TMP+2:06X}
 asl a
 asl a
 asl a
 asl a
 clc
 adc.l ${FB:06X}
 sta.l $002116
 lda.l ${TMP:06X}
 xba
 and.w #$00ff
 sec
 sbc.w #$0020
 asl a
 asl a
 asl a
 asl a
 asl a
 ora.w #$8000
 sta.l ${TMP+4:06X}
 lda.l ${TMP:06X}
 and.w #$00ff
 clc
 adc.w #$00a1
 sta.l ${TMP+6:06X}
 phd
 lda.w #$1e00
 tcd
 sep.b #$20
 lda.b #$80
 sta.l $002115
 rep.b #$20
 ldy.w #$0000
kup1:
 lda [$08],y
 sta.l $002118
 iny
 iny
 cpy.w #$0020
 bne kup1
 pld
 lda.l $7e1aeb
 sta.l $002116
 sep.b #$20
 pla
 xba
 lda.l ${TMP+2:06X}
 ply
 plx
 plp
 rts

kwd:
 ldx.w $1aed
 lda.l $a00000,x
 cmp.b #$01
 bcc kwd_r
 cmp.b #$09
 bcs kwd_r
 sta.l ${TMP:06X}
 lda.l $a00001,x
 sta.l ${TMP+1:06X}
 jsr kup
 inx
 pha
 rep.b #$20
 inc.w $1aed
 sep.b #$20
 pla
kwd_r:
 rtl

kwe:
 ldx.w $1aed
 lda.l $a1d000,x
 cmp.b #$01
 bcc kwe_r
 cmp.b #$09
 bcs kwe_r
 sta.l ${TMP:06X}
 lda.l $a1d001,x
 sta.l ${TMP+1:06X}
 jsr kup
 inx
 pha
 rep.b #$20
 inc.w $1aed
 sep.b #$20
 pla
kwe_r:
 rtl

kw4:
 lda.l $a00000,x
 cmp.b #$01
 bcc kw4_r
 cmp.b #$09
 bcs kw4_r
 sta.l ${TMP:06X}
 xba
 cmp.b #$16
 beq kw4c
 lda.l ${TMP:06X}
 ora.b #$80
 bra kw4s
kw4c:
 lda.l ${TMP:06X}
 ora.b #$c0
kw4s:
 xba
 inx
 lda.l $a00000,x
kw4_r:
 rtl

kw5:
 lda [$90],y
 bmi kw5k
 sta.l $002118
 rtl
kw5k:
 sta.l ${TMP+8:06X}
 sep.b #$20
 lda.l ${TMP+9:06X}
 and.b #$0f
 sta.l ${TMP:06X}
 lda.l ${TMP+8:06X}
 sta.l ${TMP+1:06X}
 lda.l ${TMP+9:06X}
 and.b #$40
 beq kw5w
 lda.b #$16
 bra kw5x
kw5w:
 lda.b #$1e
kw5x:
 xba
 jsr kup
 rep.b #$20
 sta.l $002118
 rtl
'''
ST, BPOS, BVA, BUD, BLINE = 0x7E1E10, 0x7E1E12, 0x7E1E14, 0x7E1E16, 0x7E1E18
code += f'''
myblit:
 php
 rep.b #$30
 lda.l ${ST:06X}
 bne mb_res
 lda.l $7e1af5
 asl a
 tax
 lda.l $999574,x
 sta.l ${BPOS:06X}
 lda.w #$0000
 sta.l ${BLINE:06X}
 lda.l $998ca8
 sta.l ${BVA:06X}
 lda.w #$0001
 sta.l ${ST:06X}
mb_res:
 lda.w #$0004
 sta.l ${BUD:06X}
mb_loop:
 lda.l ${BPOS:06X}
 tax
 lda.l $7e0000,x
 cmp.w #$00ff
 bne mb1
 lda.l ${BLINE:06X}
 inc a
 sta.l ${BLINE:06X}
 asl a
 tax
 lda.l $998ca8,x
 sta.l ${BVA:06X}
 bra mb_next2
mb1:
 cmp.w #$00fa
 bne mb2
 lda.w #$0000
 sta.l ${ST:06X}
 sta.l $7e1b1d
 plp
 rtl
mb2:
 bit.w #$8000
 beq mb_norm
 sta.l ${TMP+8:06X}
 lda.l ${BUD:06X}
 bne mb3
 plp
 rtl
mb3:
 dec a
 sta.l ${BUD:06X}
 lda.l ${BVA:06X}
 sta.l $7e1aeb
 sta.l $002116
 sep.b #$20
 lda.l ${TMP+9:06X}
 and.b #$0f
 sta.l ${TMP:06X}
 lda.l ${TMP+8:06X}
 sta.l ${TMP+1:06X}
 lda.l ${TMP+9:06X}
 and.b #$40
 beq mb4
 lda.b #$16
 bra mb5
mb4:
 lda.b #$1e
mb5:
 xba
 jsr kup
 rep.b #$20
 sta.l $002118
 bra mb_next
mb_norm:
 pha
 lda.l ${BVA:06X}
 sta.l $002116
 pla
 sta.l $002118
mb_next:
 lda.l ${BVA:06X}
 inc a
 sta.l ${BVA:06X}
mb_next2:
 lda.l ${BPOS:06X}
 inc a
 inc a
 sta.l ${BPOS:06X}
 jmp mb_loop

boxclr:
 php
 rep.b #$20
 lda.w #$0000
 sta.l ${ST:06X}
 lda.w #$00a3
 jml $9994CA
'''
code += extras.asm_code()
hook, L = asm(code, 0xBF8000)
put(0xBF8000, hook)
print('hook bytes', len(hook))

def jsl(a): return bytes([0x22, a & 255, (a >> 8) & 255, a >> 16])
expect(0x99F4A3, '08c220c210'); put(0x99F4A3, bytes([0x5c, L['fonthook'] & 255, (L['fonthook'] >> 8) & 255, 0xBF]))
expect(0x99858D, 'aeed1abf00008d'); put(0x99858D, jsl(L['kwd']) + b'\xea\xea\xea')
expect(0x99970D, 'aeed1abf00008d'); put(0x99970D, jsl(L['kwd']) + b'\xea\xea\xea')
expect(0x99D906, 'aeed1abf00d0a1'); put(0x99D906, jsl(L['kwe']) + b'\xea\xea\xea')
expect(0x999533, 'bf00008d'); put(0x999533, jsl(L['kw4']))
expect(0x9995BB, 'b7908d1821'); put(0x9995BB, jsl(L['kw5']) + b'\xea')

expect(0x999475, 'adf51a2084959c1d1b8000'); put(0x999475, jsl(L['myblit']) + bytes([0x80, 0x05]))
expect(0x9994C4, '08c220a9a300'); put(0x9994C4, bytes([0x5c, L['boxclr'] & 255, (L['boxclr'] >> 8) & 255, 0xBF]))
extras.apply(rom, put, expect, off, L)

# ---------------- checksum ----------------
rom[0x7fdc:0x7fe0] = b'\xff\xff\x00\x00'
s = sum(rom) & 0xffff
rom[0x7fdc:0x7fe0] = bytes([(s ^ 0xffff) & 255, (s ^ 0xffff) >> 8, s & 255, s >> 8])
open(dst, 'wb').write(rom)
print('SHA-256', hashlib.sha256(bytes(rom)).hexdigest())
print('written', dst, hashlib.sha256(rom).hexdigest()[:16])

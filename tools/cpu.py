"""Minimal 65816 interpreter for tracing game code from a snes9x savestate (LoROM)."""
import struct


class Mem:
    def __init__(self, rom, wram, sram=None):
        self.rom = rom; self.wram = bytearray(wram); self.io = bytearray(0x10000)
        self.sram = bytearray(sram or b'\0' * 0x8000)
        self.wlog = None; self.rlog = None
        self.mula = 0; self.mulb = 0; self.dividend = 0

    def romoff(self, a):
        bank = (a >> 16) & 0x7f
        return (bank * 0x8000 + (a & 0x7fff)) % len(self.rom)

    def r(self, a):
        a &= 0xffffff; bank = a >> 16; off = a & 0xffff
        if self.rlog is not None: self.rlog(a)
        if bank in (0x7e, 0x7f): return self.wram[(bank - 0x7e) * 0x10000 + off]
        b = bank & 0x7f
        if b < 0x40 or (bank & 0x7f) >= 0x40:
            if b < 0x40 or b < 0x70:
                pass
        if b < 0x40:
            if off < 0x2000: return self.wram[off]
            if off < 0x8000:
                if off == 0x4212:
                    self.tog = getattr(self, 'tog', 0) + 1
                    return 0x80 if (self.tog // 4) % 2 == 0 else 0x01
                if off == 0x4210: return 0x82
                return self.io[off]
            return self.rom[self.romoff(a)]
        if 0x70 <= b < 0x7e and off < 0x8000: return self.sram[off % len(self.sram)]
        if off >= 0x8000: return self.rom[self.romoff(a)]
        return self.rom[self.romoff(a | 0x8000)]

    def w(self, a, v):
        a &= 0xffffff; bank = a >> 16; off = a & 0xffff; v &= 0xff
        if self.wlog is not None: self.wlog(a, v)
        if bank in (0x7e, 0x7f): self.wram[(bank - 0x7e) * 0x10000 + off] = v; return
        b = bank & 0x7f
        if b < 0x40:
            if off < 0x2000: self.wram[off] = v; return
            if off < 0x8000:
                self.io[off] = v
                if off == 0x4203:
                    p = self.io[0x4202] * v; self.io[0x4216] = p & 255; self.io[0x4217] = p >> 8
                if off == 0x4206:
                    d = self.io[0x4204] | self.io[0x4205] << 8
                    q, r = (d // v, d % v) if v else (0xffff, d)
                    self.io[0x4214] = q & 255; self.io[0x4215] = q >> 8; self.io[0x4216] = r & 255; self.io[0x4217] = r >> 8
                if off == 0x2180:
                    wa = self.io[0x2181] | self.io[0x2182] << 8 | (self.io[0x2183] & 1) << 16
                    self.wram[wa] = v; wa = (wa + 1) & 0x1ffff
                    self.io[0x2181] = wa & 255; self.io[0x2182] = (wa >> 8) & 255; self.io[0x2183] = wa >> 16
                return
            return
        if 0x70 <= b < 0x7e and off < 0x8000: self.sram[off % len(self.sram)] = v


class CPU:
    def __init__(self, mem, regs):
        self.m = mem
        self.PB = regs['PB']; self.DB = regs['DB']; self.P = regs['P'] & 0xff; self.A = regs['A']; self.D = regs['D']
        self.S = regs['S']; self.X = regs['X']; self.Y = regs['Y']; self.PC = regs['PC']; self.E = 0
        self.trace = None; self.steps = 0

    # flags
    def fm(self): return self.P & 0x20
    def fx(self): return self.P & 0x10

    def setnz(self, v, w16):
        self.P &= ~0x82
        if w16:
            if v & 0xffff == 0: self.P |= 2
            if v & 0x8000: self.P |= 0x80
        else:
            if v & 0xff == 0: self.P |= 2
            if v & 0x80: self.P |= 0x80

    def r8(self, a): return self.m.r(a)
    def r16(self, a): return self.m.r(a) | self.m.r((a & 0xff0000) | ((a + 1) & 0xffff)) << 8
    def r16l(self, a): return self.m.r(a) | self.m.r(a + 1) << 8
    def w8(self, a, v): self.m.w(a, v)
    def w16(self, a, v): self.m.w(a, v & 255); self.m.w(a + 1, (v >> 8) & 255)

    def fetch(self):
        v = self.m.r(self.PB << 16 | self.PC); self.PC = (self.PC + 1) & 0xffff; return v

    def fetch16(self): lo = self.fetch(); return lo | self.fetch() << 8
    def fetch24(self): lo = self.fetch16(); return lo | self.fetch() << 16

    def push8(self, v): self.m.w(self.S, v); self.S = (self.S - 1) & 0xffff
    def pull8(self): self.S = (self.S + 1) & 0xffff; return self.m.r(self.S)
    def push16(self, v): self.push8(v >> 8); self.push8(v & 255)
    def pull16(self): lo = self.pull8(); return lo | self.pull8() << 8

    # addressing: returns effective 24-bit address
    def ea(self, mode):
        D = self.D; DB = self.DB << 16
        if mode == 'dp': return (D + self.fetch()) & 0xffff
        if mode == 'dpx': return (D + self.fetch() + self.X) & 0xffff
        if mode == 'dpy': return (D + self.fetch() + self.Y) & 0xffff
        if mode == 'abs': return DB | self.fetch16()
        if mode == 'absx': return (DB | self.fetch16()) + self.X & 0xffffff
        if mode == 'absy': return (DB | self.fetch16()) + self.Y & 0xffffff
        if mode == 'long': return self.fetch24()
        if mode == 'longx': return (self.fetch24() + self.X) & 0xffffff
        if mode == 'dpi': p = (D + self.fetch()) & 0xffff; return DB | self.r16(p)
        if mode == 'dpiy': p = (D + self.fetch()) & 0xffff; return ((DB | self.r16(p)) + self.Y) & 0xffffff
        if mode == 'dpxi': p = (D + self.fetch() + self.X) & 0xffff; return DB | self.r16(p)
        if mode == 'dpil': p = (D + self.fetch()) & 0xffff; return self.r16(p) | self.m.r(p + 2) << 16
        if mode == 'dpily': p = (D + self.fetch()) & 0xffff; return ((self.r16(p) | self.m.r(p + 2) << 16) + self.Y) & 0xffffff
        if mode == 'sr': return (self.S + self.fetch()) & 0xffff
        if mode == 'sriy': p = (self.S + self.fetch()) & 0xffff; return ((DB | self.r16(p)) + self.Y) & 0xffffff
        raise Exception(mode)

    def load(self, mode, w16):
        if mode == 'imm': return self.fetch16() if w16 else self.fetch()
        a = self.ea(mode)
        return self.r16l(a) if w16 else self.r8(a)

    def store(self, mode, v, w16):
        a = self.ea(mode)
        if w16: self.w16(a, v)
        else: self.w8(a, v)

    def rmw(self, mode, fn):
        w16 = not self.fm()
        if mode == 'acc':
            if w16: self.A = fn(self.A, True) & 0xffff
            else: self.A = (self.A & 0xff00) | (fn(self.A & 255, False) & 255)
            return
        a = self.ea(mode)
        if w16: self.w16(a, fn(self.r16l(a), True))
        else: self.w8(a, fn(self.r8(a), False))

    def step(self):
        pc0 = self.PB << 16 | self.PC
        op = self.fetch()
        if self.trace: self.trace(pc0, op, self)
        self.steps += 1
        G = OPS.get(op)
        if G is None: raise Exception(f'op {op:02X} at {pc0:06X}')
        G(self)


M8 = 'imm dp dpx abs absx absy long longx dpi dpiy dpxi dpil dpily sr sriy'.split()
GRP = {0x00: 'dpxi', 0x02: 'sr', 0x04: 'dp', 0x06: 'dpil', 0x08: 'imm', 0x0c: 'abs', 0x0e: 'long',
       0x10: 'dpiy', 0x12: 'dpi', 0x14: 'dpx', 0x16: 'dpily', 0x18: 'absy', 0x1c: 'absx', 0x1e: 'longx'}
OPS = {}


def acc_op(base, fn):
    for k, mode in GRP.items():
        op = base | (k + 1 if k != 0x02 else 0x03)
    for low, mode in [(0x01, 'dpxi'), (0x03, 'sr'), (0x05, 'dp'), (0x07, 'dpil'), (0x09, 'imm'), (0x0d, 'abs'), (0x0f, 'long'),
                      (0x11, 'dpiy'), (0x12, 'dpi'), (0x13, 'sriy'), (0x15, 'dpx'), (0x17, 'dpily'), (0x19, 'absy'), (0x1d, 'absx'),
                      (0x1f, 'longx')]:
        def f(c, mode=mode):
            w16 = not c.fm(); v = c.load(mode, w16); fn(c, v, w16)
        OPS[base | low] = f


def _ora(c, v, w):
    if w: c.A = (c.A | v) & 0xffff
    else: c.A = (c.A & 0xff00) | ((c.A | v) & 0xff)
    c.setnz(c.A, w)


def _and(c, v, w):
    if w: c.A = c.A & v
    else: c.A = (c.A & 0xff00) | (c.A & v & 0xff)
    c.setnz(c.A, w)


def _eor(c, v, w):
    if w: c.A = (c.A ^ v) & 0xffff
    else: c.A = (c.A & 0xff00) | ((c.A ^ v) & 0xff)
    c.setnz(c.A, w)


def _adc(c, v, w):
    a = c.A if w else c.A & 0xff; cy = c.P & 1; mask = 0xffff if w else 0xff; sign = 0x8000 if w else 0x80
    if c.P & 8:
        # decimal
        res = 0; carry = cy
        for sh in range(0, 16 if w else 8, 4):
            d = ((a >> sh) & 15) + ((v >> sh) & 15) + carry
            carry = 1 if d > 9 else 0
            if carry: d -= 10
            res |= (d & 15) << sh
        r = res; cout = carry
    else:
        r = a + v + cy; cout = 1 if r > mask else 0; r &= mask
    c.P &= ~0x41
    if cout: c.P |= 1
    if (~(a ^ v) & (a ^ r)) & sign: c.P |= 0x40
    if w: c.A = r
    else: c.A = (c.A & 0xff00) | r
    c.setnz(r, w)


def _sbc(c, v, w):
    mask = 0xffff if w else 0xff
    if c.P & 8:
        a = c.A if w else c.A & 0xff; cy = c.P & 1; borrow = 1 - cy; res = 0
        for sh in range(0, 16 if w else 8, 4):
            d = ((a >> sh) & 15) - ((v >> sh) & 15) - borrow
            borrow = 1 if d < 0 else 0
            if borrow: d += 10
            res |= (d & 15) << sh
        sign = 0x8000 if w else 0x80
        c.P &= ~0x41
        if not borrow: c.P |= 1
        if ((a ^ v) & (a ^ res)) & sign: c.P |= 0x40
        if w: c.A = res
        else: c.A = (c.A & 0xff00) | res
        c.setnz(res, w)
    else:
        _adc(c, (~v) & mask, w)


def _cmpv(c, reg, v, w):
    mask = 0xffff if w else 0xff
    r = (reg & mask) - v
    c.P &= ~1
    if r >= 0: c.P |= 1
    c.setnz(r & mask, w)


def _cmp(c, v, w): _cmpv(c, c.A, v, w)


def _lda(c, v, w):
    if w: c.A = v
    else: c.A = (c.A & 0xff00) | v
    c.setnz(v, w)


acc_op(0x00, _ora); acc_op(0x20, _and); acc_op(0x40, _eor); acc_op(0x60, _adc); acc_op(0xa0, _lda); acc_op(0xc0, _cmp); acc_op(0xe0, _sbc)
# STA
for low, mode in [(0x01, 'dpxi'), (0x03, 'sr'), (0x05, 'dp'), (0x07, 'dpil'), (0x0d, 'abs'), (0x0f, 'long'), (0x11, 'dpiy'),
                  (0x12, 'dpi'), (0x13, 'sriy'), (0x15, 'dpx'), (0x17, 'dpily'), (0x19, 'absy'), (0x1d, 'absx'), (0x1f, 'longx')]:
    OPS[0x80 | low] = lambda c, mode=mode: c.store(mode, c.A, not c.fm())


def xop(op, mode, kind):
    def f(c):
        w = not c.fx()
        if kind == 'ldx': v = c.load(mode, w); c.X = v; c.setnz(v, w)
        elif kind == 'ldy': v = c.load(mode, w); c.Y = v; c.setnz(v, w)
        elif kind == 'stx': c.store(mode, c.X, w)
        elif kind == 'sty': c.store(mode, c.Y, w)
        elif kind == 'cpx': _cmpv(c, c.X, c.load(mode, w), w)
        elif kind == 'cpy': _cmpv(c, c.Y, c.load(mode, w), w)
    OPS[op] = f


for op, mode in [(0xa2, 'imm'), (0xa6, 'dp'), (0xb6, 'dpy'), (0xae, 'abs'), (0xbe, 'absy')]: xop(op, mode, 'ldx')
for op, mode in [(0xa0, 'imm'), (0xa4, 'dp'), (0xb4, 'dpx'), (0xac, 'abs'), (0xbc, 'absx')]: xop(op, mode, 'ldy')
for op, mode in [(0x86, 'dp'), (0x96, 'dpy'), (0x8e, 'abs')]: xop(op, mode, 'stx')
for op, mode in [(0x84, 'dp'), (0x94, 'dpx'), (0x8c, 'abs')]: xop(op, mode, 'sty')
for op, mode in [(0xe0, 'imm'), (0xe4, 'dp'), (0xec, 'abs')]: xop(op, mode, 'cpx')
for op, mode in [(0xc0, 'imm'), (0xc4, 'dp'), (0xcc, 'abs')]: xop(op, mode, 'cpy')
for op, mode in [(0x64, 'dp'), (0x74, 'dpx'), (0x9c, 'abs'), (0x9e, 'absx')]:
    OPS[op] = lambda c, mode=mode: c.store(mode, 0, not c.fm())


def bitop(mode):
    def f(c):
        w = not c.fm(); v = c.load(mode, w); a = c.A if w else c.A & 0xff
        c.P &= ~2
        if (a & v) == 0: c.P |= 2
        if mode != 'imm':
            c.P &= ~0xc0
            c.P |= (v >> (8 if w else 0)) & 0xc0
    return f


for op, mode in [(0x89, 'imm'), (0x24, 'dp'), (0x34, 'dpx'), (0x2c, 'abs'), (0x3c, 'absx')]: OPS[op] = bitop(mode)


def shift(fn):
    return fn


def asl(v, w): c = CUR[0]; m = 0xffff if w else 0xff; c.P = (c.P & ~1) | ((v >> (15 if w else 7)) & 1); r = (v << 1) & m; c.setnz(r, w); return r
def lsr(v, w): c = CUR[0]; c.P = (c.P & ~1) | (v & 1); r = v >> 1; c.setnz(r, w); return r
def rol(v, w): c = CUR[0]; m = 0xffff if w else 0xff; cy = c.P & 1; c.P = (c.P & ~1) | ((v >> (15 if w else 7)) & 1); r = ((v << 1) | cy) & m; c.setnz(r, w); return r
def ror(v, w): c = CUR[0]; cy = c.P & 1; c.P = (c.P & ~1) | (v & 1); r = (v >> 1) | (cy << (15 if w else 7)); c.setnz(r, w); return r
def inc(v, w): c = CUR[0]; r = (v + 1) & (0xffff if w else 0xff); c.setnz(r, w); return r
def dec(v, w): c = CUR[0]; r = (v - 1) & (0xffff if w else 0xff); c.setnz(r, w); return r


CUR = [None]
for base, fn in [(0x00, asl), (0x40, lsr), (0x20, rol), (0x60, ror)]:
    for low, mode in [(0x06, 'dp'), (0x16, 'dpx'), (0x0e, 'abs'), (0x1e, 'absx'), (0x0a, 'acc')]:
        OPS[base | low] = lambda c, mode=mode, fn=fn: (CUR.__setitem__(0, c), c.rmw(mode, fn))
for op, mode in [(0xe6, 'dp'), (0xf6, 'dpx'), (0xee, 'abs'), (0xfe, 'absx'), (0x1a, 'acc')]:
    OPS[op] = lambda c, mode=mode: (CUR.__setitem__(0, c), c.rmw(mode, inc))
for op, mode in [(0xc6, 'dp'), (0xd6, 'dpx'), (0xce, 'abs'), (0xde, 'absx'), (0x3a, 'acc')]:
    OPS[op] = lambda c, mode=mode: (CUR.__setitem__(0, c), c.rmw(mode, dec))


def tsbtrb(mode, set_):
    def f(c):
        w = not c.fm(); a = c.ea(mode); v = c.r16l(a) if w else c.r8(a); acc = c.A if w else c.A & 0xff
        c.P &= ~2
        if (acc & v) == 0: c.P |= 2
        r = (v | acc) if set_ else (v & ~acc)
        if w: c.w16(a, r)
        else: c.w8(a, r)
    return f


OPS[0x04] = tsbtrb('dp', 1); OPS[0x0c] = tsbtrb('abs', 1); OPS[0x14] = tsbtrb('dp', 0); OPS[0x1c] = tsbtrb('abs', 0)


def branch(cond):
    def f(c):
        o = c.fetch()
        if cond(c): c.PC = (c.PC + (o - 256 if o > 127 else o)) & 0xffff
    return f


OPS[0x10] = branch(lambda c: not c.P & 0x80); OPS[0x30] = branch(lambda c: c.P & 0x80)
OPS[0x50] = branch(lambda c: not c.P & 0x40); OPS[0x70] = branch(lambda c: c.P & 0x40)
OPS[0x90] = branch(lambda c: not c.P & 1); OPS[0xb0] = branch(lambda c: c.P & 1)
OPS[0xd0] = branch(lambda c: not c.P & 2); OPS[0xf0] = branch(lambda c: c.P & 2)
OPS[0x80] = branch(lambda c: True)


def brl(c):
    o = c.fetch16(); c.PC = (c.PC + (o - 65536 if o > 32767 else o)) & 0xffff


OPS[0x82] = brl
for op, bit, val in [(0x18, 1, 0), (0x38, 1, 1), (0x58, 4, 0), (0x78, 4, 1), (0xb8, 0x40, 0), (0xd8, 8, 0), (0xf8, 8, 1)]:
    OPS[op] = lambda c, bit=bit, val=val: setattr(c, 'P', (c.P | bit) if val else (c.P & ~bit))


def fixx(c):
    if c.P & 0x10: c.X &= 0xff; c.Y &= 0xff


def rep(c): c.P &= ~c.fetch(); fixx(c)
def sep(c): c.P |= c.fetch(); fixx(c)


OPS[0xc2] = rep; OPS[0xe2] = sep


def xce(c):
    cy = c.P & 1; c.P = (c.P & ~1) | c.E; c.E = cy
    if c.E: c.P |= 0x30; fixx(c)


OPS[0xfb] = xce


def tr(src, dst, flagx=False, nz=True):
    def f(c):
        v = getattr(c, src)
        if dst in ('X', 'Y'):
            w = not c.fx(); v = v if w else v & 0xff; setattr(c, dst, v)
        elif dst == 'A':
            w = not c.fm()
            if w: c.A = v & 0xffff
            else: c.A = (c.A & 0xff00) | (v & 0xff)
        else:
            w = True; setattr(c, dst, v & 0xffff)
        if nz: c.setnz(v, w)
    return f


OPS[0xaa] = tr('A', 'X'); OPS[0xa8] = tr('A', 'Y'); OPS[0x8a] = tr('X', 'A'); OPS[0x98] = tr('Y', 'A')
OPS[0x9b] = tr('X', 'Y'); OPS[0xbb] = tr('Y', 'X'); OPS[0xba] = tr('S', 'X'); OPS[0x9a] = tr('X', 'S', nz=False)


def tcd(c): c.D = c.A; c.setnz(c.A, True)
def tdc(c): c.A = c.D; c.setnz(c.A, True)
def tcs(c): c.S = c.A
def tsc(c): c.A = c.S; c.setnz(c.A, True)
def xba(c): c.A = ((c.A >> 8) | (c.A << 8)) & 0xffff; c.setnz(c.A & 0xff, False)


OPS[0x5b] = tcd; OPS[0x7b] = tdc; OPS[0x1b] = tcs; OPS[0x3b] = tsc; OPS[0xeb] = xba
OPS[0xe8] = lambda c: (setattr(c, 'X', (c.X + 1) & (0xff if c.fx() else 0xffff)), c.setnz(c.X, not c.fx()))
OPS[0xca] = lambda c: (setattr(c, 'X', (c.X - 1) & (0xff if c.fx() else 0xffff)), c.setnz(c.X, not c.fx()))
OPS[0xc8] = lambda c: (setattr(c, 'Y', (c.Y + 1) & (0xff if c.fx() else 0xffff)), c.setnz(c.Y, not c.fx()))
OPS[0x88] = lambda c: (setattr(c, 'Y', (c.Y - 1) & (0xff if c.fx() else 0xffff)), c.setnz(c.Y, not c.fx()))


def pha(c):
    if c.fm(): c.push8(c.A & 255)
    else: c.push16(c.A)


def pla(c):
    if c.fm(): c.A = (c.A & 0xff00) | c.pull8(); c.setnz(c.A, False)
    else: c.A = c.pull16(); c.setnz(c.A, True)


def phr(r):
    def f(c):
        if c.fx(): c.push8(getattr(c, r) & 255)
        else: c.push16(getattr(c, r))
    return f


def plr(r):
    def f(c):
        if c.fx(): v = c.pull8()
        else: v = c.pull16()
        setattr(c, r, v); c.setnz(v, not c.fx())
    return f


OPS[0x48] = pha; OPS[0x68] = pla; OPS[0xda] = phr('X'); OPS[0xfa] = plr('X'); OPS[0x5a] = phr('Y'); OPS[0x7a] = plr('Y')
OPS[0x08] = lambda c: c.push8(c.P)
def plp(c): c.P = c.pull8(); fixx(c)
OPS[0x28] = plp
OPS[0x8b] = lambda c: c.push8(c.DB)
def plb(c): c.DB = c.pull8(); c.setnz(c.DB, False)
OPS[0xab] = plb
OPS[0x4b] = lambda c: c.push8(c.PB)
OPS[0x0b] = lambda c: c.push16(c.D)
def pld(c): c.D = c.pull16(); c.setnz(c.D, True)
OPS[0x2b] = pld
OPS[0xf4] = lambda c: c.push16(c.fetch16())
def pei(c): p = (c.D + c.fetch()) & 0xffff; c.push16(c.r16(p))
OPS[0xd4] = pei
def per(c): o = c.fetch16(); c.push16((c.PC + o) & 0xffff)
OPS[0x62] = per


def jmp_abs(c): c.PC = c.fetch16()
def jmp_ind(c): a = c.fetch16(); c.PC = c.r16(a)
def jmp_indx(c): a = c.fetch16(); c.PC = c.r16(c.PB << 16 | ((a + c.X) & 0xffff))
def jml(c): a = c.fetch24(); c.PC = a & 0xffff; c.PB = a >> 16
def jml_ind(c): a = c.fetch16(); c.PC = c.r16l(a); c.PB = c.m.r(a + 2)
def jsr(c): a = c.fetch16(); c.push16((c.PC - 1) & 0xffff); c.PC = a
def jsr_indx(c): a = c.fetch16(); c.push16((c.PC - 1) & 0xffff); c.PC = c.r16(c.PB << 16 | ((a + c.X) & 0xffff))
def jsl(c): a = c.fetch24(); c.push8(c.PB); c.push16((c.PC - 1) & 0xffff); c.PC = a & 0xffff; c.PB = a >> 16
def rts(c): c.PC = (c.pull16() + 1) & 0xffff
def rtl(c): c.PC = (c.pull16() + 1) & 0xffff; c.PB = c.pull8()
def rti(c): c.P = c.pull8(); fixx(c); c.PC = c.pull16(); c.PB = c.pull8()


OPS.update({0x4c: jmp_abs, 0x6c: jmp_ind, 0x7c: jmp_indx, 0x5c: jml, 0xdc: jml_ind, 0x20: jsr, 0xfc: jsr_indx, 0x22: jsl,
            0x60: rts, 0x6b: rtl, 0x40: rti, 0xea: lambda c: None, 0x42: lambda c: c.fetch()})


def mvn(c, step):
    dst = c.fetch(); src = c.fetch(); c.DB = dst
    while True:
        c.m.w(dst << 16 | c.Y, c.m.r(src << 16 | c.X))
        c.X = (c.X + step) & 0xffff; c.Y = (c.Y + step) & 0xffff
        c.A = (c.A - 1) & 0xffff
        if c.A == 0xffff: break


OPS[0x54] = lambda c: mvn(c, 1); OPS[0x44] = lambda c: mvn(c, -1)


def wai(c): raise StopIteration('WAI')


OPS[0xcb] = wai


def regs_from_state(s):
    i = s.find(b'REG:000016:') + 11
    PB, DB, P, A, D, S, X, Y, PC = struct.unpack('>BBHHHHHHH', s[i:i + 16])
    return dict(PB=PB, DB=DB, P=P, A=A, D=D, S=S, X=X, Y=Y, PC=PC)


def from_state(rom, state):
    i = state.find(b'RAM:131072:') + 11
    wram = state[i:i + 131072]
    return CPU(Mem(rom, wram), regs_from_state(state))

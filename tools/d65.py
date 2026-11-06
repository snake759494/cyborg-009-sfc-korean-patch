import sys
MN = ("BRK ORA COP ORA TSB ORA ASL ORA PHP ORA ASL PHD TSB ORA ASL ORA "
      "BPL ORA ORA ORA TRB ORA ASL ORA CLC ORA INC TCS TRB ORA ASL ORA "
      "JSR AND JSL AND BIT AND ROL AND PLP AND ROL PLD BIT AND ROL AND "
      "BMI AND AND AND BIT AND ROL AND SEC AND DEC TSC BIT AND ROL AND "
      "RTI EOR WDM EOR MVP EOR LSR EOR PHA EOR LSR PHK JMP EOR LSR EOR "
      "BVC EOR EOR EOR MVN EOR LSR EOR CLI EOR PHY TCD JML EOR LSR EOR "
      "RTS ADC PER ADC STZ ADC ROR ADC PLA ADC ROR RTL JMP ADC ROR ADC "
      "BVS ADC ADC ADC STZ ADC ROR ADC SEI ADC PLY TDC JMP ADC ROR ADC "
      "BRA STA BRL STA STY STA STX STA DEY BIT TXA PHB STY STA STX STA "
      "BCC STA STA STA STY STA STX STA TYA STA TXS TXY STZ STA STZ STA "
      "LDY LDA LDX LDA LDY LDA LDX LDA TAY LDA TAX PLB LDY LDA LDX LDA "
      "BCS LDA LDA LDA LDY LDA LDX LDA CLV LDA TSX TYX LDY LDA LDX LDA "
      "CPY CMP REP CMP CPY CMP DEC CMP INY CMP DEX WAI CPY CMP DEC CMP "
      "BNE CMP CMP CMP PEI CMP DEC CMP CLD CMP PHX STP JML CMP DEC CMP "
      "CPX SBC SEP SBC CPX SBC INC SBC INX SBC NOP XBA CPX SBC INC SBC "
      "BEQ SBC SBC SBC PEA SBC INC SBC SED SBC PLX XCE JSR SBC INC SBC").split()
# addressing modes per low nibble pattern (standard 65816 table)
AM = {}
for op in range(256):
    lo = op & 0x1f
    AM[op] = None
modes = ("imp dpxi imm sr dp dp dp dpil imp immm imp imp abs abs abs long "
         "rel dpiy dpi sriy dp dpx dpx dpily imp absy imp imp abs absx absx longx").split()
for op in range(256):
    AM[op] = modes[op & 0x1f]
fix = {0x00: 'imm', 0x02: 'imm', 0x20: 'abs', 0x22: 'long', 0x40: 'imp', 0x44: 'mv', 0x54: 'mv', 0x60: 'imp', 0x62: 'rell',
       0x6b: 'imp', 0x80: 'rel', 0x82: 'rell', 0x89: 'immm', 0xa0: 'immx', 0xa2: 'immx', 0xc0: 'immx', 0xe0: 'immx',
       0xc2: 'imm', 0xe2: 'imm', 0xd4: 'dpi', 0xf4: 'abs', 0x6c: 'absi', 0x7c: 'absxi', 0xdc: 'absil', 0xfc: 'absxi',
       0x5c: 'long', 0x14: 'dp', 0x1c: 'abs', 0x04: 'dp', 0x0c: 'abs', 0x34: 'dpx', 0x3c: 'absx', 0x24: 'dp', 0x2c: 'abs',
       0x64: 'dp', 0x74: 'dpx', 0x9c: 'abs', 0x9e: 'absx', 0x96: 'dpy', 0xb6: 'dpy', 0xbe: 'absy', 0x84: 'dp', 0x86: 'dp',
       0x8c: 'abs', 0x8e: 'abs', 0x94: 'dpx', 0xa4: 'dp', 0xa6: 'dp', 0xac: 'abs', 0xae: 'abs', 0xb4: 'dpx', 0xbc: 'absx',
       0xc4: 'dp', 0xcc: 'abs', 0xe4: 'dp', 0xec: 'abs', 0x06: 'dp', 0x0e: 'abs', 0x16: 'dpx', 0x1e: 'absx', 0x26: 'dp',
       0x2e: 'abs', 0x36: 'dpx', 0x3e: 'absx', 0x46: 'dp', 0x4e: 'abs', 0x56: 'dpx', 0x5e: 'absx', 0x66: 'dp', 0x6e: 'abs',
       0x76: 'dpx', 0x7e: 'absx', 0xc6: 'dp', 0xce: 'abs', 0xd6: 'dpx', 0xde: 'absx', 0xe6: 'dp', 0xee: 'abs', 0xf6: 'dpx',
       0xfe: 'absx', 0x4c: 'abs', 0x62: 'rell'}
for k in range(256):
    if (k & 0x1f) in (0x0a, 0x1a, 0x1b, 0x0b, 0x08, 0x18, 0x0d - 0x0d + 0x08):
        pass
AM.update(fix)
for k in (0x0a, 0x2a, 0x4a, 0x6a, 0x1a, 0x3a, 0x5a, 0x7a, 0xda, 0xfa, 0x8a, 0x9a, 0xaa, 0xba, 0xca, 0xea, 0x0b, 0x1b, 0x2b,
          0x3b, 0x4b, 0x5b, 0x6b, 0x7b, 0x8b, 0x9b, 0xab, 0xbb, 0xcb, 0xdb, 0xeb, 0xfb, 0x08, 0x18, 0x28, 0x38, 0x48, 0x58,
          0x68, 0x78, 0x88, 0x98, 0xa8, 0xb8, 0xc8, 0xd8, 0xe8, 0xf8, 0x40, 0x60, 0x6b):
    AM[k] = 'imp'
SZ = dict(imp=0, dpxi=1, imm=1, sr=1, dp=1, dpil=1, abs=2, long=3, rel=1, dpiy=1, dpi=1, sriy=1, dpx=1, dpy=1, dpily=1,
          absy=2, absx=2, longx=3, mv=2, rell=2, absi=2, absxi=2, absil=2)


def dis(rom, start, end, m=1, x=1, out=print):
    p = start
    while p < end:
        op = rom[p]; mode = AM[op]
        if mode == 'immm': n = 1 if m else 2; mode = 'imm'
        elif mode == 'immx': n = 1 if x else 2; mode = 'imm'
        else: n = SZ[mode]
        b = rom[p + 1:p + 1 + n]; v = int.from_bytes(b, 'little')
        snes = ((p >> 15) << 16) | (p & 0x7fff) | 0x8000
        fmt = {'imp': '', 'imm': f'#${v:0{2*n}X}', 'dp': f'${v:02X}', 'dpx': f'${v:02X},x', 'dpy': f'${v:02X},y',
               'dpi': f'(${v:02X})', 'dpxi': f'(${v:02X},x)', 'dpiy': f'(${v:02X}),y', 'dpil': f'[${v:02X}]',
               'dpily': f'[${v:02X}],y', 'sr': f'${v:02X},s', 'sriy': f'(${v:02X},s),y', 'abs': f'${v:04X}',
               'absx': f'${v:04X},x', 'absy': f'${v:04X},y', 'long': f'${v:06X}', 'longx': f'${v:06X},x',
               'mv': f'${b[0]:02X},${b[1]:02X}' if len(b) == 2 else '', 'absi': f'(${v:04X})', 'absxi': f'(${v:04X},x)',
               'absil': f'[${v:04X}]'}.get(mode, '')
        if mode == 'rel': fmt = f'${(snes + 2 + (v - 256 if v > 127 else v)) & 0xffff:04X}'
        if mode == 'rell': fmt = f'${(snes + 3 + (v - 65536 if v > 32767 else v)) & 0xffff:04X}'
        out(f'{p:06X} {snes:06X} {rom[p:p+1+n].hex(" "):12s} {MN[op]} {fmt}')
        if op == 0xc2:
            if v & 0x20: m = 0
            if v & 0x10: x = 0
        if op == 0xe2:
            if v & 0x20: m = 1
            if v & 0x10: x = 1
        p += 1 + n


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    dis(rom, int(sys.argv[2], 16), int(sys.argv[3], 16), int(sys.argv[4]) if len(sys.argv) > 4 else 1,
        int(sys.argv[5]) if len(sys.argv) > 5 else 1)

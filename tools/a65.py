"""Tiny 65816 assembler. Syntax: 'op.s operand' where s in b/w/l picks operand size.
modes: #imm, addr, addr,x, addr,y, (dp), (dp),y, [dp], [dp],y, label (branch / jsr / jml)."""
import re,sys
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from d65 import MN, AM
OP={}
for op in range(256):
    m=AM[op]; OP.setdefault((MN[op],m),op)
def num(s,labels):
    s=s.strip()
    if s in labels: return labels[s]
    if s.startswith('$'): return int(s[1:],16)
    return int(s,0)
def asm(src, org):
    lines=[l.split(';')[0].rstrip() for l in src.split('\n')]
    for p in range(2):
        labels = getattr(asm,'_labels',{}) if p==1 else {}
        pc=org; out=bytearray()
        for l in lines:
            if not l.strip(): continue
            if l.strip().endswith(':'): labels[l.strip()[:-1]]=pc; continue
            parts=l.split(None,1); ins=parts[0].lower(); arg=parts[1].strip() if len(parts)>1 else ''
            mn,_,sz=ins.partition('.'); mn=mn.upper()
            if mn=='DB':
                bs=[num(x,labels) if p else 0 for x in arg.split(',')]; out+=bytes(b&255 for b in bs); pc+=len(bs); continue
            if mn=='DW':
                for x in arg.split(','):
                    v=num(x,labels) if p else 0; out+=bytes([v&255,(v>>8)&255]); pc+=2
                continue
            if mn=='DL':
                for x in arg.split(','):
                    v=num(x,labels) if p else 0; out+=bytes([v&255,(v>>8)&255,(v>>16)&255]); pc+=3
                continue
            def val(x):
                try: return num(x,labels)
                except Exception:
                    if p: raise
                    return 0
            if mn in ('BRA','BEQ','BNE','BCC','BCS','BPL','BMI','BVC','BVS'):
                op=OP[(mn,'rel')]; t=val(arg); d=t-(pc+2)
                if p and not -128<=d<128: raise Exception('branch range '+l)
                out+=bytes([op,d&255]); pc+=2; continue
            if mn=='BRL':
                t=val(arg); d=t-(pc+3); out+=bytes([0x82,d&255,(d>>8)&255]); pc+=3; continue
            if mn in ('JSR','JMP') and sz!='l' and not arg.startswith('('):
                op=0x20 if mn=='JSR' else 0x4c; v=val(arg); out+=bytes([op,v&255,(v>>8)&255]); pc+=3; continue
            if mn in ('JSL','JML') or (mn in('JSR','JMP') and sz=='l'):
                op=0x22 if mn in('JSL','JSR') else 0x5c; v=val(arg); out+=bytes([op,v&255,(v>>8)&255,(v>>16)&255]); pc+=4; continue
            if mn in ('MVN','MVP'):
                a,b=arg.split(','); out+=bytes([0x54 if mn=='MVN' else 0x44,val(a),val(b)]); pc+=3; continue
            if not arg or arg.lower()=='a': mode='imp'; n=0
            elif arg.startswith('#'):
                v=val(arg[1:]); n={'b':1,'w':2}[sz]; mode='immm' if (mn,'immm') in OP else ('immx' if (mn,'immx') in OP else 'imm')
                if mn in('REP','SEP'): mode='imm'; n=1
            else:
                m=re.match(r'^\((.*)\),y$',arg,re.I) or re.match(r'^\[(.*)\],y$',arg,re.I)
                ind = arg[0] if arg[0] in '([' else ''
                base=arg
                suf=''
                if arg.lower().endswith(',x'): suf='x'; base=arg[:-2]
                elif arg.lower().endswith(',y'): suf='y'; base=arg[:-2]
                if ind=='(':
                    inner=base.strip('()')
                    if suf=='y': mode='dpiy'
                    elif inner.lower().endswith(',x'): mode='dpxi'; inner=inner[:-2]
                    else: mode='dpi'
                    v=val(inner); n=1
                elif ind=='[':
                    v=val(base.strip('[]')); n=1; mode='dpily' if suf=='y' else 'dpil'
                else:
                    v=val(base); n={'b':1,'w':2,'l':3}[sz]
                    mode={(1,''):'dp',(1,'x'):'dpx',(1,'y'):'dpy',(2,''):'abs',(2,'x'):'absx',(2,'y'):'absy',(3,''):'long',(3,'x'):'longx'}[(n,suf)]
            key=(mn,mode)
            if key not in OP: raise Exception(f'no op {key} in "{l}"')
            op=OP[key]; out.append(op)
            if mode=='imp': pc+=1; continue
            out+=bytes([(v>>(8*i))&255 for i in range(n)]); pc+=1+n
        asm._labels=labels
    asm._labels={}
    return bytes(out),labels

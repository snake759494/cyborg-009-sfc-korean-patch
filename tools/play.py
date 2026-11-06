# usage: play.py rom state_in|- state_out prefix "seq"   seq: e.g. "A*20:90 START:60 wait:300 R:30"
import sys; sys.path.insert(0,'tools')
from emu import Emu
rom,sin,sout,pre,seq=sys.argv[1:6]
e=Emu(rom)
if sin!='-': e.load(sin)
i=0
for tok in seq.split():
    k,_,n=tok.partition(':'); n=int(n or 60)
    rep=1
    if '*' in k: k,r=k.split('*'); rep=int(r)
    for _ in range(rep):
        if k!='wait': e.tap(k)
        e.run(n)
        if pre!='-': e.shot(f'shots/{pre}{i:03d}.png',1)
        i+=1
if sout!='-': e.save(sout)
e.close()

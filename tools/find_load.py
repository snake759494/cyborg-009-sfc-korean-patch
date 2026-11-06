import sys; sys.path.insert(0,'tools')
from emu import Emu
e=Emu('../Cyborg 009 (Japan).sfc')
seq=[(300,None)]+[(60,'START')]*6+[(60,'A')]*2+[(200,None)]
target=open('vram.bin','rb').read()[0xae40:0xae60]  # イ glyph
prev=None
for n,k in seq:
    if k: e.tap(k,hold=3,after=0)
    for f in range(n):
        st=e.save()
        e.run(1)
        if e.vram()[0xae40:0xae60]==target:
            open('st_before.bin','wb').write(prev or st); print('frame',e.frame); e.close(); sys.exit()
        prev=st

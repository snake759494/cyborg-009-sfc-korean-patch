import sys; sys.path.insert(0,'tools')
from emu import Emu
e=Emu('../Cyborg 009 (Japan).sfc')
prev=None
def tm(v): return v[0x8000+11*64:0x8000+17*64]
base=None
for f in range(1200):
    st=e.save(); e.run(1)
    t=tm(e.vram())
    if base is None: base=t
    if t!=base and any(t):
        open('st_pro.bin','wb').write(st); print('frame',e.frame); break
    base=t
e.close()

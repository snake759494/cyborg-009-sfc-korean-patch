import sys; sys.path.insert(0,'tools')
from emu import Emu
e=Emu('../Cyborg 009 (Japan).sfc')
seq=[(300,None)]+[(60,'START')]*6+[(60,'A')]*2+[(200,None)]
for n,k in seq:
    if k: e.tap(k)
    e.run(n)
e.shot('shots/d1.png',2)
open('vram.bin','wb').write(e.vram()); open('wram.bin','wb').write(e.wram())
e.save('st_d1.bin'); e.close()

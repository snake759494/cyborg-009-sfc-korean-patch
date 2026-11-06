import sys; sys.path.insert(0,'tools')
from emu import Emu
e=Emu('../Cyborg 009 (Japan).sfc')
e.run(90*4+30); e.shot('shots/p.png',2)
open('vram_p.bin','wb').write(e.vram()); e.save('st_p.bin'); e.close()

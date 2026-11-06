import sys; sys.path.insert(0,'tools')
from emu import Emu
e=Emu(sys.argv[1] if len(sys.argv)>1 else '../Cyborg 009 (Japan).sfc')
for i in range(48):
    e.run(90); e.shot(f'shots/a{i:03d}.png',1)
e.close()

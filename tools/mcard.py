import sys; sys.path.insert(0,'tools')
from emu import Emu
e=Emu(sys.argv[1]); e.load('st_title.bin')
e.tap('START'); 
for i in range(200):
    e.run(1)
e.shot('shots/mc.png',2); open('vram_mc.bin','wb').write(e.vram()); e.save('st_mc.bin'); e.close()

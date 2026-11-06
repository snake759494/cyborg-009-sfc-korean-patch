import sys, ctypes as C; sys.path.insert(0,'tools')
from emu import Emu
rom,st,mode,pre=sys.argv[1],sys.argv[2],int(sys.argv[3],16),sys.argv[4]
pokes=[(int(a,16),int(v,16)) for a,v in (p.split('=') for p in sys.argv[5:] if '=' in p)]
e=Emu(rom); e.load(st)
p=e.core.retro_get_memory_data(2)
def poke(a,v): C.memmove(p+a, bytes([v]),1)
poke(0x208,mode&255); poke(0x209,0)
for a,v in pokes: poke(a,v)
for i in range(int(__import__("os").environ.get("N","30"))):
    if i>3 and '--noa' not in sys.argv: e.tap('A',3,0)
    for f in range(60):
        e.run(1)
    e.shot(f'shots/{pre}{i:02d}.png',1)
e.save('st_'+pre+'.bin'); e.close()

import sys; sys.path.insert(0,'tools')
from emu import Emu
e=Emu(sys.argv[1])
seq=[(300,None)]+[(60,'START')]*6+[(90,'A')]*30
for i,(n,k) in enumerate(seq):
    if k: e.tap(k)
    e.run(n)
    if i>=6: e.shot(f'shots/k{i:03d}.png',1)
e.save('st_k.bin'); e.close()

import sys; sys.path.insert(0, sys.argv[1])
from emu import Emu
e = Emu(sys.argv[2])
seq = [(300,None)]+[(60,'START')]*6+[(60,'A')]*40
for i,(n,k) in enumerate(seq):
    if k: e.tap(k)
    e.run(n)
    if i%3==0: e.shot(f'{sys.argv[3]}/s{i:03d}.png',1)
e.save(sys.argv[3]+'/st.bin')
e.close()

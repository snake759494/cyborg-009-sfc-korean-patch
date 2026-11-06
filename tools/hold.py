import sys; sys.path.insert(0,'tools')
from emu import Emu
e=Emu(sys.argv[1]); e.load(sys.argv[2])
for i,k in enumerate(['START','A','B','SELECT','X','Y','L','R']):
    st=e.save()
    e.run(30,[k]); e.run(120)
    e.shot(f'shots/h{i}_{k}.png',1)
    e.load(st)
e.close()

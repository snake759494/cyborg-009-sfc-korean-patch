import sys,collections; sys.path.insert(0,'tools')
from trace import run_frames
rom=open('../Cyborg 009 (Japan).sfc','rb').read()
st=open(sys.argv[1],'rb').read()
rr=collections.defaultdict(list); cur=[0,0]
def onstep(pc,op,c): cur[0]=pc
def onread(c,a):
    b=(a>>16)&0x7f; o=a&0xffff
    if b<0x40 and o>=0x8000 and not (0<= (a&0x7fffff)-(cur[0]&0x7fffff) <4):
        rr[cur[0]].append(a)
c=run_frames(rom,st,frames=int(sys.argv[2]),on_step=onstep,on_read=onread)
for pc,l in sorted(rr.items(), key=lambda x:-len(x[1]))[:30]:
    print(hex(pc),len(l),hex(min(l)),hex(max(l)))

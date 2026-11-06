import sys,collections; sys.path.insert(0,'tools')
from trace import run_frames
rom=open('../Cyborg 009 (Japan).sfc','rb').read()
st=open(sys.argv[1],'rb').read()
romreads=collections.Counter(); vw=collections.Counter(); dma=[]
cur=[0]
def onstep(pc,op,c): cur[0]=pc
def onread(c,a):
    b=a>>16; o=a&0xffff
    if (b&0x7f)<0x40 and o>=0x8000: romreads[cur[0]]+=1
def onwrite(c,a,v):
    o=a&0xffff
    if (a>>16)&0x7f<0x40 and o in (0x2118,0x2119): vw[cur[0]]+=1
    if (a>>16)&0x7f<0x40 and o==0x420b:
        io=c.m.io; 
        for ch in range(8):
            if v&(1<<ch):
                b=0x4300+ch*16
                dma.append((hex(cur[0]),ch,hex(io[b]),hex(io[b+1]),hex(io[b+2]|io[b+3]<<8|io[b+4]<<16),hex(io[b+5]|io[b+6]<<8), hex(c.m.wram[0x2116] if False else 0)))
c=run_frames(rom,st,frames=int(sys.argv[2]),on_step=onstep,on_read=onread,on_write=onwrite)
print('romreads',[(hex(a),n) for a,n in romreads.most_common(25)])
print('vramw',[(hex(a),n) for a,n in vw.most_common(10)])
for x in dma[:40]: print(x)

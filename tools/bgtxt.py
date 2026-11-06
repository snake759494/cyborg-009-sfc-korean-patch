import sys; sys.path.insert(0,'tools')
import lzss
CH='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
INV={}
for n,c in enumerate(CH):
  p=n+1; INV[(p%8)*2+(p//8)*0x20]=c
def show(d,label):
  for q in range(len(d)//2048):
    for row in range(32):
      w=[d[q*2048+(row*32+c)*2]|d[q*2048+(row*32+c)*2+1]<<8 for c in range(32)]
      s=''
      for x in w:
        t=x&0x3ff
        s+= INV.get(t,'.') if x else ' '
      if s.strip(): print(label,q,row,s)
if __name__=='__main__':
  r=open(sys.argv[1],'rb').read()
  for k in map(int,sys.argv[2:]):
    show(lzss.decomp(r,lzss.lo2pc(lzss.table(r)[k]))[0],k)

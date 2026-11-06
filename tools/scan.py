import sys; sys.path.insert(0,'tools')
import lzss
from emu import Emu
rom=sys.argv[1]; st=sys.argv[2]
e=Emu(rom); e.load(st); e.run(2); v=e.vram(); e.close()
r=open(rom,'rb').read()
for i,a in enumerate(lzss.table(r)):
  if a&0x8000==0: continue
  try: d=lzss.decomp(r,lzss.lo2pc(a))[0]
  except: continue
  if len(d)<64: continue
  for k in range(0,0x10000,0x100):
    seg=v[k:k+min(len(d),0x10000-k)]
    if len(seg)>=64 and seg==d[:len(seg)] and d[:64].strip(b'\0'):
      print('asset',i,'vram word',hex(k//2),'len',len(d)); break

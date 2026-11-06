import sys; sys.path.insert(0,'tools')
import lzss
rom=sys.argv[1]; v=open(sys.argv[2],'rb').read(); words=[int(x,16) for x in sys.argv[3:]]
r=open(rom,'rb').read()
D={}
for i,a in enumerate(lzss.table(r)):
  if a&0x8000==0: continue
  try: D[i]=lzss.decomp(r,lzss.lo2pc(a))[0]
  except: pass
for w in words:
  t=v[w*2:w*2+32]
  hits=[(i,hex(d.find(t))) for i,d in D.items() if d.find(t)>=0]
  print(hex(w),t.hex()[:16],hits[:5])

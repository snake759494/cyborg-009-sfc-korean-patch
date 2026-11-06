import sys; sys.path.insert(0,'tools')
from emu import Emu
from PIL import Image, ImageDraw
rom,st,out=sys.argv[1:4]
e=Emu(rom); e.load(st); e.run(2); v=e.vram(); e.close()
open(out+'.bin','wb').write(v)
im=Image.new('L',(32*8,(2048//32)*8))
for t in range(2048):
  b=v[t*32:t*32+32]
  for y in range(8):
    for x in range(8):
      p=((b[y*2]>>(7-x))&1)|((b[y*2+1]>>(7-x))&1)<<1|((b[16+y*2]>>(7-x))&1)<<2|((b[17+y*2]>>(7-x))&1)<<3
      im.putpixel(((t%32)*8+x,(t//32)*8+y),p*17)
im=im.resize((im.width*2,im.height*2)).convert('RGB'); d=ImageDraw.Draw(im)
for j in range(0,im.height,64): d.text((0,j),hex(j//64*0x200),fill=(255,0,0))
im.save(out+'.png')

import sys; sys.path.insert(0,'tools')
import lzss
from PIL import Image, ImageDraw
rom=sys.argv[1]; idx=int(sys.argv[2]); out=sys.argv[3]; W=int(sys.argv[4]) if len(sys.argv)>4 else 16
r=open(rom,'rb').read(); d=lzss.decomp(r,lzss.lo2pc(lzss.table(r)[idx]))[0]
n=len(d)//32
im=Image.new('RGB',(W*8,((n+W-1)//W)*8),(0,0,80))
for k in range(n):
  b=d[k*32:k*32+32]
  for y in range(8):
    for x in range(8):
      p=((b[y*2]>>(7-x))&1)|((b[y*2+1]>>(7-x))&1)<<1|((b[16+y*2]>>(7-x))&1)<<2|((b[17+y*2]>>(7-x))&1)<<3
      if p: im.putpixel(((k%W)*8+x,(k//W)*8+y),(p*17,p*17,p*17))
S=3; im=im.resize((im.width*S,im.height*S),Image.NEAREST); dr=ImageDraw.Draw(im)
for j in range(0,im.height,8*S*2): dr.text((0,j),hex(j//(8*S)*W),fill=(255,60,60))
im.save(out)

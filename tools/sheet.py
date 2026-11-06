import sys,glob
from PIL import Image
fs=sorted(glob.glob(sys.argv[1]))[:int(sys.argv[3]) if len(sys.argv)>3 else 16]
ims=[Image.open(f) for f in fs]; w,h=ims[0].size; c=4
S=Image.new('RGB',(w*c,h*((len(ims)+c-1)//c)))
for i,im in enumerate(ims): S.paste(im,((i%c)*w,(i//c)*h))
S.save(sys.argv[2])

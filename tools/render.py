from PIL import Image
def tiles(data,bpp=4,cols=16,scale=1):
    tb=8*bpp; n=len(data)//tb
    im=Image.new('L',(cols*8,((n+cols-1)//cols)*8))
    px=im.load()
    for t in range(n):
        for y in range(8):
            for x in range(8):
                c=0
                for p in range(bpp):
                    o=t*tb+(p//2)*16+y*2+(p&1)
                    c|=((data[o]>>(7-x))&1)<<p
                px[(t%cols)*8+x,(t//cols)*8+y]=c*255//((1<<bpp)-1)
    return im.resize((im.width*scale,im.height*scale),Image.NEAREST)

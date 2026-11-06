from PIL import Image, ImageDraw, ImageFont
import os
HERE=os.path.dirname(os.path.abspath(__file__))
PAGES=[["세계 정복을 꾀하던","조직에 의해 사이보그가","된 젊은이들이 있었다."],
       ["그들은 자신을 만든","조직과 싸워","승리를 거두었다."],
       ["사람들은","9명의 전사를","사이보그 009라 불렀다."],
       ["그리고 지금...","세계 평화를 위협하는","새로운 적이","움직이기 시작했다."]]
def render(fontfile,size,thr=110,dy=0):
    f=ImageFont.truetype(open(os.path.join(HERE,'..','work','fonts',fontfile),'rb'),size)
    pages=[]
    for P in PAGES:
        im=Image.new('L',(256,len(P)*16))
        d=ImageDraw.Draw(im)
        for i,l in enumerate(P):
            w=d.textlength(l,font=f)
            x=(256-w)//2
            x=int(x)//1
            d.text((x,i*16+dy),l,font=f,fill=255)
        pages.append(im.point(lambda v:255 if v>thr else 0))
    return pages
def tiles_of(pages):
    uniq={}; maps=[]
    for im in pages:
        m=[]
        for ty in range(im.height//8):
            row=[]
            for tx in range(32):
                t=bytes(im.crop((tx*8,ty*8,tx*8+8,ty*8+8)).tobytes())
                if t not in uniq: uniq[t]=len(uniq)
                row.append(uniq[t])
            m.append(row)
        maps.append(m)
    return uniq,maps
if __name__=='__main__':
    for fn,sz in (('NanumSquareNeo-cBd.ttf',11),('NanumSquareNeo-cBd.ttf',12),('NanumSquareNeo-bRg.ttf',12)):
        p=render(fn,sz); u,_=tiles_of(p); print(fn,sz,len(u))
        S=Image.new('L',(256,sum(i.height+8 for i in p)));y=0
        for i in p: S.paste(i,(0,y)); y+=i.height+8
        S.resize((512,S.height*2)).save(f'shots/pro_{sz}_{fn[15:18]}.png')

def lo2pc(a): return ((a>>16)&0x7f)*0x8000+(a&0x7fff)
def decomp(d,p):
    size=d[p]|d[p+1]<<8; q=p+4
    win=bytearray(0x1000); r=0xfee; out=bytearray(); flags=0
    while len(out)<size:
        flags>>=1
        if not flags&0x100: flags=d[q]|0xff00; q+=1
        if flags&1:
            c=d[q]; q+=1; out.append(c); win[r]=c; r=(r+1)&0xfff
        else:
            lo=d[q]; hi=d[q+1]; q+=2
            off=lo|(hi&0xf0)<<4; n=(hi&0xf)+3
            for k in range(n):
                if len(out)>=size: break
                c=win[(off+k)&0xfff]; out.append(c); win[r]=c; r=(r+1)&0xfff
    return bytes(out), q-p
def table(d):
    res=[]
    for i in range(200):
        o=0x6de33+i*3
        if o+3>0x6dfdc: break
        a=d[o]|d[o+1]<<8|d[o+2]<<16
        res.append(a)
    return res
if __name__=='__main__':
    d=open('../Cyborg 009 (Japan).sfc','rb').read()
    for i,a in enumerate(table(d)):
        if a&0x8000==0: print(i,hex(a),'?'); continue
        p=lo2pc(a)
        try:
            o,n=decomp(d,p); print(i,hex(a),hex(p),len(o),n)
        except Exception as ex: print(i,hex(a),'ERR',ex)

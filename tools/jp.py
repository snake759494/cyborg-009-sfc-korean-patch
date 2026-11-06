H='ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ'
hira='あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん'
kata='アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン'
small_h={0xa6:'を',0xa7:'ぁ',0xa8:'ぃ',0xa9:'ぅ',0xaa:'ぇ',0xab:'ぉ',0xac:'ゃ',0xad:'ゅ',0xae:'ょ',0xaf:'っ',0xb0:'ー',0xa1:'。',0xa2:'「',0xa3:'」',0xa4:'、',0xa5:'・',0xde:'゛',0xdf:'゜'}
def ch(b):
    if 0xb1<=b<=0xdd: return hira[b-0xb1]
    if b in small_h: return small_h[b]
    if 0x71<=b<=0x9d: return kata[b-0x71]
    if 0x66<=b<=0x70: return {0x66:'ヲ',0x67:'ァ',0x68:'ィ',0x69:'ゥ',0x6a:'ェ',0x6b:'ォ',0x6c:'ャ',0x6d:'ュ',0x6e:'ョ',0x6f:'ッ',0x70:'ー'}[b]
    if 0x20<=b<0x60: return chr(b)
    return None
def dec(d,a,b):
    out='';i=a
    while i<b:
        x=d[i]; c=ch(x)
        if c is None: out+=f'[{x:02X}]'
        else: out+=c
        if x==0xff: out+='\n'
        i+=1
    return out
if __name__=='__main__':
    import sys
    d=open(sys.argv[1],'rb').read()
    print(dec(d,int(sys.argv[2],16),int(sys.argv[3],16)))

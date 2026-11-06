import json,sys
sys.path.insert(0,'tools')
from jp import ch
R=open('../Cyborg 009 (Japan).sfc','rb').read()
w=lambda o:R[o]|R[o+1]<<8
DAK={'か':'が','き':'ぎ','く':'ぐ','け':'げ','こ':'ご','さ':'ざ','し':'じ','す':'ず','せ':'ぜ','そ':'ぞ','た':'だ','ち':'ぢ','つ':'づ','て':'で','と':'ど','は':'ば','ひ':'び','ふ':'ぶ','へ':'べ','ほ':'ぼ','ウ':'ヴ'}
HAN={'は':'ぱ','ひ':'ぴ','ふ':'ぷ','へ':'ぺ','ほ':'ぽ'}
def kat(c):
    return chr(ord(c)+0x60) if 'ぁ'<=c<='ゖ' else c
def deco(o):
    s='';i=o
    while True:
        b=R[i]
        if b==0xFA: s+='[FA]'; i+=1; break
        if b==0xFF: s+='\n'
        elif b in (0xDE,0xDF) and s:
            prev=s[-1]; h=chr(ord(prev)-0x60) if 'ァ'<=prev<='ヶ' else prev
            t=(DAK if b==0xDE else HAN).get(h)
            if t: s=s[:-1]+(kat(t) if h!=prev else t)
            else: s+=f'[{b:02X}]'
        elif 0xE0<=b<=0xE9: s+='{'+str(b-0xE0)+'}'
        elif b>=0xF0 or b<0x20: s+=f'[{b:02X}]'
        else:
            c=ch(b); s+=c if c else f'[{b:02X}]'
        i+=1
    return s,i-o
out=[]
D=0x68000  # bank 0D base for $C000 rel -> 0x6C000
def rel(r): return 0x6c000+r
seen={}
def add(key,addr):
    if addr in seen: seen[addr]['refs'].append(key); return
    s,n=deco(addr); e={'id':key,'addr':hex(addr),'len':n,'refs':[key],'jp':s,'ko':''}
    seen[addr]=e; out.append(e)
for i in range(6): add(f'D.intro{i}',rel(w(0x6c6fa+i*2)))
for i in range(8): add(f'D.prof{i}',rel(w(0x6d186+i*2)))
for i in range(8): add(f'D.call{i}',rel(w(0x6d317+i*2)))
for k,r in (('D.sel_ok',0x13a7),('D.sel_1',0x13be),('D.sel_2',0x13eb),('D.sel_go',0x1418)): add(k,rel(r))
B=0x8d000
for g in range(5):
    t=B+w(B+6+g*2)
    for m in range(8): add(f'E.m{g}c{m}',B+w(t+m*2))
for m in range(8): add(f'E.g1c{m}',B+w(B+0x63e+m*2))
for g in range(4): add(f'E.g2m{g}',B+w(B+0x6fb+g*2))
json.dump(out,open('script_jp.json','w',encoding='utf8'),ensure_ascii=False,indent=1)
print(len(out), sum(e['len'] for e in out))
for e in out: print(e['id'],e['addr'],e['len'],e['refs'][1:] if len(e['refs'])>1 else '')

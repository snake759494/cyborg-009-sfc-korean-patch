import sys
d=open('../Cyborg 009 (Japan).sfc','rb').read()
sj='ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをん'
go='あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽぁぃぅぇぉっゃゅょ'
for name,tab in (('sjis',sj),('gojuon',go)):
  for w in sys.argv[1:]:
    v=[tab.index(c) for c in w]
    df=[v[i+1]-v[i] for i in range(len(v)-1)]
    for step in (1,2):
      for i in range(0,len(d)-len(v)*step):
        ok=True
        for j,x in enumerate(df):
          a=d[i+j*step]; b=d[i+(j+1)*step]
          if (b-a)&0xff!=x&0xff: ok=False;break
        if ok: print(name,w,step,hex(i),d[i:i+len(v)*step].hex())

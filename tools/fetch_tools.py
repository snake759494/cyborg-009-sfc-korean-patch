# -*- coding: utf-8 -*-
"""빌드에 필요한 글꼴을 work/fonts/에 준비하고 SHA-256을 대조한다.
- 갈무리 v2.40.3 (quiple/galmuri, SIL OFL 1.1): Galmuri7.ttf·Galmuri9.ttf 를 공식 릴리즈에서 받는다.
- 나눔스퀘어 네오 (NAVER, SIL OFL 1.1) bRg·cBd·dEb·eHv: https://hangeul.naver.com/font
- 서울한강체 EB (서울특별시): https://www.seoul.go.kr/seoul/font.do
  위 두 글꼴은 공식 배포처에서 직접 받아 work/fonts/에 넣는다."""
import hashlib, io, json, os, urllib.request, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'work', 'fonts'); os.makedirs(DST, exist_ok=True)
GALMURI = 'https://github.com/quiple/galmuri/releases/download/v2.40.3/Galmuri-v2.40.3.zip'
WANT = json.load(open(os.path.join(ROOT, 'release_manifest.json'), encoding='utf-8'))['fonts']

need = [f for f in ('Galmuri7.ttf', 'Galmuri9.ttf') if not os.path.exists(os.path.join(DST, f))]
if need:
    print('받는 중', GALMURI)
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(GALMURI).read()))
    for info in z.infolist():
        if os.path.basename(info.filename) in need:
            open(os.path.join(DST, os.path.basename(info.filename)), 'wb').write(z.read(info))
ok = True
for f, h in WANT.items():
    p = os.path.join(DST, f)
    if not os.path.exists(p):
        print('없음', f, '- 공식 배포처에서 받아 work/fonts/에 넣으세요'); ok = False; continue
    got = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    print('확인' if got == h else '해시 불일치', f); ok &= got == h
raise SystemExit(0 if ok else 1)

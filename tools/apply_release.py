# -*- coding: utf-8 -*-
"""원본 ROM에 릴리즈 xdelta를 적용하고 원본·패치·결과 해시를 확인한다.
사용: python tools/apply_release.py 원본.sfc Cyborg_009_SFC_KR.xdelta 결과.sfc [--xdelta xdelta3.exe]"""
import argparse, hashlib, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
man = json.load(open(os.path.join(ROOT, 'release_manifest.json'), encoding='utf-8'))['files']
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

ap = argparse.ArgumentParser()
ap.add_argument('source'); ap.add_argument('patch'); ap.add_argument('output')
ap.add_argument('--xdelta', default='xdelta3')
a = ap.parse_args()
for key, path in (('source', a.source), ('patch', a.patch)):
    ok = sha(path) == man[key]['sha256']
    print(key, '일치' if ok else '불일치', path)
    if not ok: sys.exit(1)
subprocess.run([a.xdelta, '-D', '-d', '-f', '-s', a.source, a.patch, a.output], check=True)
ok = sha(a.output) == man['output']['sha256']
print('output', '일치' if ok else '불일치', a.output)
sys.exit(0 if ok else 1)

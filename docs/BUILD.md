# 빌드

Windows, Python 3.10 이상에서 확인했습니다.

```powershell
pip install -r requirements.txt
# 나눔스퀘어 네오(bRg·cBd·dEb·eHv)와 서울한강체 EB(SeoulHangangEB.ttf)를 공식 배포처에서 받아 work/fonts/ 에 넣습니다.
python tools/fetch_tools.py          # 갈무리7·9 v2.40.3을 work/fonts/에 받고 모든 글꼴의 해시 대조
python tools/build.py 'Cyborg 009 (Japan).sfc' 'work/Cyborg 009 (Korean).sfc'
xdelta3 -f -0 -S none -D -e -s 'Cyborg 009 (Japan).sfc' 'work/Cyborg 009 (Korean).sfc' Cyborg_009_SFC_KR.xdelta
```

- `build.py`는 원본 ROM(1,048,576바이트, 헤더 없음)의 SHA-256을 먼저 검사합니다. 글꼴 판이 다르면 결과 ROM도 달라집니다.
- 출력의 `SHA-256` 줄이 README의 `output`과 같으면 릴리즈와 동일한 ROM입니다.
- 대사 형식(`translation/script_ko.txt`): `## 키` 줄로 묶음을 나누고, 본문 줄바꿈은 게임 줄바꿈입니다. `[XX]`는 원본 제어 바이트입니다(`[FE]` 다음 페이지, `[FA]` 묶음 끝 등). 묶음은 반드시 `[FA]`로 끝나야 합니다.
- `tools/extract.py`는 원본 ROM에서 일본어 대사를 뽑아 번역 대조용 파일을 만듭니다(결과물은 저장소에 포함하지 않음).
- `tools/emu.py`·`play.py`·`fresh.py`는 검증용 헤드리스 snes9x 하네스이며 `snes9x_libretro.dll`을 따로 받아 `tools/`에 두어야 합니다(저장소에 포함하지 않음).

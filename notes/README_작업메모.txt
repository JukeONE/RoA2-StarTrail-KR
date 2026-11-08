아카니아 왕국 2 (Star Trail Classic, Steam) 한글패치 작업 메모 — 2026-11-03

[확인된 것]
- STAR.DAT: 4바이트 개수(1242) + 항목 20바이트(이름14, 오프셋4, 2) / 데이터 시작 = 4+개수*20-2
  -> tools/parse.py(추출), tools/repack.py(재포장, 무수정 재포장 시 원본과 동일 확인)
- 텍스트: *.LTX(0x00 구분 문자열, @=줄바꿈, ^=공백, 0xF0~F5/0x7E=색상 제어), *.TLK(대화, 구조 미분석), *.INF(고정 길이 칸)
- 글꼴 FONT.NVF: 1바이트 타입, 2바이트 개수(87), 글자별 (폭,높이) 4바이트, 1픽셀=1바이트
- 줄 간격 = 글꼴 높이(생성자에서 +0x1a = +0x16). 한글 칸 8픽셀(갈무리7 7x7) 확정
- STAR.EXE: Borland C++ 16비트 + 오버레이(FBOV). 글꼴 모듈 세그먼트 0xd98(이미지 오프셋 0xD980, 파일 오프셋 +7680)
  DA83 글자정보 / DB1B 글리프주소 / DB79 글자그리기 / DC35 그리기+전진 / DCF8 문자열폭

[한글 출력 패치 — 게임에서 성공 확인]
- 인코딩: 첫바이트 0x80~0xA7, 둘째바이트 0xA8~0xEF (움라우트 0x81,84,8E,94,99,9A,E1 제외) = KS X 1001 한글 2350자 순서
  -> tools/krenc.py 의 enc()
- FONT.NVF 뒤(오프셋 4208)에 asm/blob.asm 코드 + 2350자 1비트 글리프(8바이트씩) 부착 = FONT_KR.NVF
- STAR.EXE: asm/hook.asm 을 DA83~DB15 자리에 덮어쓰고, DB1B·DB79 첫 6바이트를 해당 cave로 jmp

[번역 위치 메모]
- 장소 띠 "Temple of %s in %s" = TEMPLE.LTX[0], 신 이름 = GLOBLTXT.LTX[5..18]
- 난이도 창 = GLOBLTXT[0..2], 디스크 메뉴 = DISKMENU.LTX

[다음 할 일]
1. TLK 대화 파일 구조 분석  2. 추출/삽입 도구(번역 표)  3. 길이 고정 칸 조사  4. 용어집  5. 번역  6. 설치/복원 도구
글꼴: 갈무리(Galmuri) by quiple, SIL OFL 1.1

[2026-11-04 TLK 분석 결과]
- TLK 205개 중 168개는 텍스트 스크립트(따옴표 문자열). 연속된 따옴표 줄은 한 항목(공백으로 이어짐)
- 28개는 바이너리형: 파일 끝 [텍스트 길이 u16][문자열 개수 u16][0x00 구분 문자열], 개수 = NUL 수 + 1
  -> 길이 u16만 고치면 됨 (문자열은 번호로 참조되는 것으로 보임 - 게임 확인 필요)
- LOW69.TLK(데이터), PHEXNITE.TLK(이미지)는 텍스트 없음
- TOPICS.TOP: 대화 주제 이름 86개 (텍스트 스크립트형)
- 도구: tools/textdb.py extract/inject. 번역 표 text/*.json (en/ko). 무수정 재삽입 시 원본과 동일 확인
- 번역 대상: 항목 8,940개, 약 60만 자 (LTX 43.7만, TLK 스크립트 11.5만, TLK 바이너리 5.2만) - DEBUG.LTX 등 제외 가능
- KS X 1001에 없는 글자(예: 툘)는 못 씀 -> 비슷한 글자로 대체

[2026-11-04 빌드/번역 진행]
- 빌드: python3 tools/build.py 원본STAR.EXE 원본STAR.DAT 출력폴더  (EXE 패치 + 한글 글꼴 + 번역 삽입 한 번에)
- 번역 입력: tr/*.py (딕셔너리) -> python3 tr/fill.py 모듈명 -> text/*.json 에 반영. 점검: python3 tools/textdb.py check text
- 줄바꿈: 대화창은 게임이 자동 줄바꿈함 -> 번역문에는 강제 줄바꿈(\n)을 넣지 않는 것이 원칙 (KVIRASIM 에서 확인)
- 영어 대명사(he/she/his/her...)는 STAR.EXE 안 표를 빈 문자열로 패치. 번역문에서는 대명사 %s 를 앞말에 붙여 씀 (예: "다가가%s 손을")
- 빈 번역이 필요하면 ko 에 <<EMPTY>>
- 화폐 약어: 두(두카트) / 은(은화) / 동(동화)
- 번역 완료 파일: GLOBLTXT, TEMPLE, DISKMENU, TOPICS.TOP, KVIRASIM, SEQUENCE, TALKS_16, INN, SHOP, SMITH, HEALER, MARKET, KVIR01~07.TLK
- [결정] 복사 방지 문구(PROTECT.LTX)는 번역하지 않음 (passwords.pdf 영어 문서를 보고 답해야 하므로). 마을 이름은 한글로 번역
- [확인 필요] 복사 방지 "마을 이름" 질문이 GLOBLTXT 마을 이름과 비교한다면 한글 정답은 입력 불가 -> 질문이 나오면 영어 정답이 통하는지 확인
- 암호 쪽지(USE 96, 97)는 영어 원문 유지

[2026-11-04 마감 - 다음에 이어서 할 일]
- 진행률 50.0% (4,470 / 8,940 항목). 완료: 크비라심 전체, 가쇼크 전체, 로방엔 LOWANGEN.LTX + LOW01~60 TLK
- 다음 차례: LOW61, LOW62, LOW62A, LOW63, LOW65, LOW65A, LOW67, LOW68, LOW70, L_STREET (로방엔 나머지)
  -> 그다음: 티프후젠(TIEFHUS), 툴마르(TJOLMAR), 핀스터(FINSTER), 안스벨, 던전(BLUT/BINGE/PHEX 등), SPELLS, FIGHT, CAMP, MONNAMES, FINAL/OUTRO
- 작업 순서: python3 tools/dump.py LOW61.TLK ...  (미번역 항목 보기) -> tr/*.py 작성 -> python3 tr/xxx.py
  -> python3 tools/tm.py text (같은 원문 자동 채우기) -> python3 tools/textdb.py check text -> 빌드/커밋
- 용어: 두캇/은화(크라운)/동화(Bits), 화려한 비상(Colorful Flight), 아이달(Eydal), 스벨트 빨래터(Svelltwash), 넷다리(Fourbridge), 참호 늪(Trenchbog), 회색 지팡이단(Grey Staves), 파문 교단(Order of Anathema)

[일지 멈춤 버그 - 2026-11-08 해결]
- 원인: 일지 코드가 A0~A9 바이트를 표시 문자로 씀 (DS:0x48FA~0x4903).
  A0=머리말 시작, A1/A2=머리말 끝, A3=기록 끝, A4~A8=찾기 분류 태그(+ID 1바이트), A9=태그 범위 끝(부호 있는 비교).
  한글 리드(80~A7)/트레일(A8~EF)과 겹쳐서 글자가 빠지거나 깨지고, A0 리드 바이트가 단어 첫머리에 오면
  A1/A2 를 못 찾아 버퍼 밖까지 복사 -> 검은 화면 멈춤. 일지는 세이브에 들어 있어서 원본 EXE 로도 같은 세이브는 멈춤.
- 수정(build.py): 표시 바이트를 F6~FF 로 이동, 오버레이 'add al,0xA4'(EXE 0x32BD0+0x961B6) -> 0xFA,
  STAR.DAT 의 D_SEARCH.DAT 레코드(23바이트) +2 분류값도 같이 이동.
- 오버레이 위치: ovl.bin 오프셋 + 0x32BD0 = EXE 파일 오프셋. DS 베이스(이미지) = 0x247E0.
- 한글패치 이전에 만든 일지(옛 표시 바이트)는 표시가 어긋날 수 있음 -> 새로 시작 또는 일지 비어 있는 세이브 권장.

[집 PC 배포 주의]
- 같은 경로(build/STAR.DAT)를 다시 보내면 '전송 완료'로 나와도 옛 파일이 그대로 남는 경우가 있음.
  매번 deploy/STAR_<시각>.DAT 처럼 새 이름으로 복사해서 보내고, 보낸 뒤 크기를 꼭 확인할 것.

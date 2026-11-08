# 아카니아 왕국 2: 스타 트레일 한글패치 — by.김쥬크

Steam판 **Realms of Arkania 2: Star Trail Classic** (DOS, DOSBox 0.74) 한글패치입니다.

## 설치
1. [Releases](../../releases)에서 `RoA2_StarTrail_KR_v1.0.exe`를 받습니다.
2. 실행하면 Steam 게임 폴더를 자동으로 찾습니다 (못 찾으면 [찾아보기]로 직접 고르세요).
3. 화면(창 모드/전체화면, 해상도, 4:3 화면비)과 그래픽 효과를 고른 뒤 **[한글패치 설치]**.
4. Steam에서 게임을 실행합니다.

- 원본 파일은 `STAR_ORIG.EXE`, `DATA\STAR_ORIG.DAT`로 백업되고, **[원본으로 되돌리기]**로 언제든 복구할 수 있습니다.
- 설치 파일에는 게임 원본 데이터가 들어 있지 않습니다. 정품 게임 파일에 바뀐 부분만 적용합니다.
- 서명 없는 프로그램이라 Windows 경고가 뜨면 [추가 정보] → [실행]을 누르세요.

## 내용
- 게임 안 모든 대화, 이벤트, 메뉴, 아이템, 주문, 일지, 엔딩 한글화
- 7x7 한글 글꼴(갈무리) 내장, 실행 파일에 한글 2바이트 출력 코드 추가
- 원본 게임의 일지 처리 버그(한글 바이트와 표시 기호 충돌로 멈추는 문제) 수정
- 비밀번호(복사 방지) 질문은 영문 매뉴얼을 보고 답해야 하므로 영어 그대로 둡니다
- 노움 수수께끼의 답은 영어로 입력합니다 (게임에 영어 답이 고정되어 있음)

## 저장소 구성
- `text/` 한글 번역 표 (원문은 저작권 때문에 포함하지 않음)
- `tools/` STAR.DAT 재포장, 한글 인코딩, 글꼴 생성, 빌드, 설치 데이터 생성
- `asm/` 실행 파일 패치 코드 (nasm)
- `installer/` 설치 프로그램 (Win32 C, llvm-mingw로 빌드)

## 감사
- 한글 글꼴: [갈무리(Galmuri)](https://github.com/quiple/galmuri) by quiple — SIL Open Font License 1.1
- 원작: Attic Entertainment Software, FanPro / Steam판: THQ Nordic

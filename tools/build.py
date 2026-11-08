# -*- coding: utf-8 -*-
"""한글패치 빌드: 원본 STAR.EXE / STAR.DAT -> 한글판 STAR.EXE / STAR.DAT

사용법: python3 build.py 원본_STAR.EXE 원본_STAR.DAT 출력폴더
필요: fonts/Galmuri7.bdf, asm/blob.bin, asm/hook.bin, text/*.json
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import textdb  # noqa: E402
from krenc import LEADS, TRAILS, HANGUL  # noqa: E402
from mkfont import load_bdf  # noqa: E402

BLOB_AT = 4208          # FONT.NVF 안에서 한글 코드가 붙는 위치 (hook.asm 의 BLOB 과 같아야 함)
LEAD_OFF, TRAIL_OFF, GLYPH_OFF = 0x139, 0x161, 0x1E1   # blob.asm 목록 파일 기준
EXE_HDR, FONT_SEG = 7680, 0xD980                       # MZ 헤더 크기, 글꼴 모듈 세그먼트 시작
DS_BASE = 0x247E0                                      # 데이터 세그먼트 (이미지 기준)
DIARY_MARK = EXE_HDR + DS_BASE + 0x48FA                # 일지 표시 바이트 10개 (원래 A0~A9)
DIARY_ADD = 0x32BD0 + 0x961B6                          # 오버레이 안 'add al,0xA4'
DIARY_SHIFT = 0xF6 - 0xA0
PRONOUNS = b'he\0she\0it\0his\0her\0its\0him\0they\0their\0them\0hers\0'


def build_font(orig_nvf):
    blob = bytearray(open(os.path.join(ROOT, 'asm', 'blob.bin'), 'rb').read())
    assert len(blob) == GLYPH_OFF
    for i, b in enumerate(range(0x80, 0xA8)):
        blob[LEAD_OFF + i] = LEADS.index(b) if b in LEADS else 0xFF
    for i, b in enumerate(range(0xA8, 0xF0)):
        blob[TRAIL_OFF + i] = TRAILS.index(b) if b in TRAILS else 0xFF
    bdf = load_bdf(os.path.join(ROOT, 'fonts', 'Galmuri7.bdf'))
    for ch in HANGUL:                      # 한 글자 = 8줄 x 1바이트 (bit7 = 왼쪽), 7x7 글자를 아래쪽 정렬
        rows = [0] * 8
        g = bdf.get(ord(ch))
        if g:
            w, h, xo, yo = g['bbx']
            top = 8 - h - yo
            for y, r in enumerate(g['rows']):
                for x, v in enumerate(r):
                    if v and 0 <= top + y < 8 and 0 <= xo + x < 7:
                        rows[top + y] |= 0x80 >> (xo + x)
        blob += bytes(rows)
    assert len(orig_nvf) <= BLOB_AT
    return orig_nvf + b'\0' * (BLOB_AT - len(orig_nvf)) + bytes(blob)


def build_exe(orig):
    exe = bytearray(orig)
    hook = open(os.path.join(ROOT, 'asm', 'hook.bin'), 'rb').read()

    def at(o):
        return EXE_HDR + FONT_SEG + o

    def put(o, data):
        exe[at(o):at(o) + len(data)] = data

    assert exe[at(0x103):at(0x106)] == bytes.fromhex('558bec'), '원본 STAR.EXE 가 아닙니다'
    assert exe[at(0x19b):at(0x1a1)] == bytes.fromhex('558bec83ec06')
    assert exe[at(0x1f9):at(0x1ff)] == bytes.fromhex('558bec83ec0c')
    put(0x103, hook + b'\x90' * (0x196 - 0x103 - len(hook)))

    def jmp(frm, to):
        return b'\xE9' + struct.pack('<h', to - (frm + 3)) + b'\x90\x90\x90'
    put(0x19b, jmp(0x19b, 0x11a))      # DB1B 글리프 주소 -> cave
    put(0x1f9, jmp(0x1f9, 0x146))      # DB79 글자 그리기 -> cave
    # 영어 대명사(he/she/his/her...) 를 빈 문자열로: 한국어 문장에서는 생략
    p = exe.find(PRONOUNS)
    assert p > 0
    for i in range(len(PRONOUNS)):
        if PRONOUNS[i] != 0:
            exe[p + i] = 0
    # 일지 표시 바이트 A0~A9 -> F6~FF (한글 리드/트레일 바이트와 겹쳐 일지가 깨지고 게임이 멈춤)
    assert exe[DIARY_MARK:DIARY_MARK + 10] == bytes(range(0xA0, 0xAA))
    exe[DIARY_MARK:DIARY_MARK + 10] = bytes(range(0xA0 + DIARY_SHIFT, 0xAA + DIARY_SHIFT))
    assert exe[DIARY_ADD:DIARY_ADD + 2] == b'\x04\xA4'     # add al,0xA4 (찾기 분류 표시)
    exe[DIARY_ADD + 1] = 0xA4 + DIARY_SHIFT
    return bytes(exe)


def build_dsearch(data):
    """D_SEARCH.DAT: 23바이트 레코드, +2 = 분류 표시(A4~A8) -> 새 값으로"""
    d = bytearray(data)
    for i in range(0, len(d) - 22, 23):
        if 0xA4 <= d[i + 2] <= 0xA9:
            d[i + 2] += DIARY_SHIFT
    return bytes(d)


def main(exe_in, dat_in, outdir):
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'STAR.EXE'), 'wb').write(build_exe(open(exe_in, 'rb').read()))
    files = textdb.dat_load(dat_in)[6]
    font = build_font(files['FONT.NVF'])
    extra = {'FONT.NVF': font, 'D_SEARCH.DAT': build_dsearch(files['D_SEARCH.DAT'])}
    textdb.inject(dat_in, os.path.join(ROOT, 'text'), os.path.join(outdir, 'STAR.DAT'), extra=extra)
    print('빌드 완료 ->', outdir)


if __name__ == '__main__':
    main(*sys.argv[1:4])

# -*- coding: utf-8 -*-
"""설치 프로그램에 붙일 패치 데이터 만들기 (원본 게임 데이터는 넣지 않고 바뀐 부분만).

사용법: python3 mkpatch.py 원본_STAR.EXE 원본_STAR.DAT 한글_STAR.EXE 한글_STAR.DAT 출력.bin
형식(리틀 엔디언):
  'ROA2KR01'
  u32 원본EXE크기, u32 원본EXE_CRC, u32 조각수, [u32 위치, u32 길이, 바이트]...
  u32 원본DAT크기, u32 원본DAT_CRC, u32 파일수, [이름 14바이트, u32 길이, 바이트]...
"""
import struct, sys, zlib, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textdb  # noqa: E402


def exe_diff(a, b):
    assert len(a) == len(b)
    out, i = [], 0
    while i < len(a):
        if a[i] != b[i]:
            j = i
            while j < len(a) and (a[j] != b[j] or (j + 8 < len(a) and a[j:j + 8] != b[j:j + 8])):
                j += 1
            out.append((i, b[i:j]))
            i = j
        else:
            i += 1
    return out


def main(eo, do, ek, dk, outp):
    eo, ek = open(eo, 'rb').read(), open(ek, 'rb').read()
    do_b = open(do, 'rb').read()
    fo = textdb.dat_load(do)[6]
    fk = textdb.dat_load(dk)[6]
    out = bytearray(b'ROA2KR01')
    d = exe_diff(eo, ek)
    out += struct.pack('<III', len(eo), zlib.crc32(eo), len(d))
    for off, data in d:
        out += struct.pack('<II', off, len(data)) + data
    ch = [n for n in sorted(fk) if fk[n] != fo.get(n)]
    out += struct.pack('<III', len(do_b), zlib.crc32(do_b), len(ch))
    for n in ch:
        out += n.encode('latin1').ljust(14, b'\0') + struct.pack('<I', len(fk[n])) + fk[n]
    open(outp, 'wb').write(out)
    print('패치 데이터', len(out), '바이트 / EXE 조각', len(d), '/ 바뀐 파일', len(ch))


if __name__ == '__main__':
    main(*sys.argv[1:6])

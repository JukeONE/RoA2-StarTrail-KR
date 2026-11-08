#!/bin/sh
# 설치 프로그램 빌드: ./build_installer.sh <llvm-mingw 경로> <patch.bin> <출력.exe>
set -e
TC="$1"; PATCH="$2"; OUT="$3"
D=$(dirname "$0")
"$TC/bin/i686-w64-mingw32-windres" "$D/res.rc" -O coff -o /tmp/roa2kr_res.o
"$TC/bin/i686-w64-mingw32-gcc" -O2 -municode -mwindows -static -s "$D/main.c" "$D/core.c" /tmp/roa2kr_res.o \
    -lcomctl32 -lshell32 -lole32 -ladvapi32 -o "$OUT"
python3 - "$OUT" "$PATCH" <<'PY'
import sys, struct
exe, p = sys.argv[1], open(sys.argv[2], 'rb').read()
open(exe, 'ab').write(p + struct.pack('<I', len(p)) + b'RKPAYLD!')
PY
ls -l "$OUT"

# -*- coding: utf-8 -*-
"""STAR.DAT 텍스트 추출/삽입 도구.

지원 형식
  LTX  : 0x00 으로 구분된 문자열 목록
  TLK  : (1) 텍스트 스크립트형 - 따옴표 문자열, 연속된 따옴표 묶음은 한 항목
         (2) 바이너리형 - 끝부분 [길이 u16][개수 u16][0x00 구분 문자열]
  TOP  : 텍스트 스크립트형 (TOPICS.TOP)

번역 표 형식(JSON): {"file": 이름, "kind": 형식, "items": [{"id", "en", "ko"}]}
문자 표기: 줄바꿈(0x0D) -> "\\n", 독일어 움라우트 -> 유니코드, 그 밖의 제어/상위 바이트 -> {XX}
"""
import json, os, re, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from krenc import enc as kr_enc  # noqa: E402

UML = {0x84: 'ä', 0x94: 'ö', 0x81: 'ü', 0xE1: 'ß', 0x8E: 'Ä', 0x99: 'Ö', 0x9A: 'Ü'}
UML_R = {v: k for k, v in UML.items()}


# ---------------------------------------------------------------- 바이트 <-> 표기
def b2t(b: bytes) -> str:
    out = []
    for x in b:
        if x == 0x0D:
            out.append('\\n')
        elif x in UML:
            out.append(UML[x])
        elif 0x20 <= x < 0x7F and x not in (0x7B, 0x7D, 0x5C):  # { } \ 은 이스케이프
            out.append(chr(x))
        else:
            out.append('{%02X}' % x)
    return ''.join(out)


_tok = re.compile(r'\\n|\{([0-9A-Fa-f]{2})\}|.', re.S)


def t2b(s: str) -> bytes:
    out = bytearray()
    for m in _tok.finditer(s):
        t = m.group(0)
        if t == '\\n':
            out.append(0x0D)
        elif m.group(1):
            out.append(int(m.group(1), 16))
        elif t in UML_R:
            out.append(UML_R[t])
        elif ord(t) < 0x80:
            out.append(ord(t))
        else:
            out += kr_enc(t)  # 한글 -> 2바이트
    return bytes(out)


# ---------------------------------------------------------------- STAR.DAT
def dat_load(path):
    d = open(path, 'rb').read()
    n = struct.unpack('<I', d[:4])[0]
    base = 4 + n * 20 - 2
    ents = []
    for i in range(n):
        e = d[4 + i * 20:24 + i * 20]
        ents.append((e[:14].split(b'\0')[0].decode('latin1'), struct.unpack('<I', e[14:18])[0]))
    offs = sorted(set(o for _, o in ents))
    ends = offs[1:] + [len(d) - base]
    blob = {o: d[base + o:base + e] for o, e in zip(offs, ends)}
    files = {}
    for name, o in ents:
        if name and name not in files:
            files[name] = blob[o]
    return d, n, base, ents, offs, blob, files


def dat_save(src, dst, repl):
    d, n, base, ents, offs, blob, _ = dat_load(src)
    for name, o in ents:
        if name in repl:
            blob[o] = repl[name]
    newoff, cur, body = {}, 0, []
    for o in offs:
        newoff[o] = cur
        body.append(blob[o])
        cur += len(blob[o])
    hdr = bytearray(d[:base])
    for i, (_, o) in enumerate(ents):
        struct.pack_into('<I', hdr, 4 + i * 20 + 14, newoff[o])
    open(dst, 'wb').write(bytes(hdr) + b''.join(body))


# ---------------------------------------------------------------- 형식별 파서
def kind_of(name, data):
    ext = name.rsplit('.', 1)[-1]
    if ext == 'LTX':
        return 'ltx'
    if ext in ('TLK', 'TOP'):
        if data[:1] in (b'#', b'\r') or ext == 'TOP':
            return 'script'
        if data[:3] == b'AIF':
            return None
        if bin_tlk_pos(data) is not None:
            return 'bintlk'
    return None


# LTX
def ltx_items(data):
    return data.split(b'\0')


def ltx_build(parts):
    return b'\0'.join(parts)


# 바이너리 TLK
def bin_tlk_pos(data):
    for p in range(len(data) - 4):
        L, C = struct.unpack('<HH', data[p:p + 4])
        if L == len(data) - p - 4 and C == data[p + 4:].count(b'\0') + 1:
            return p
    return None


# 스크립트형: 따옴표 묶음 찾기 -> [(시작, 끝, [문자열...])]
def script_groups(data):
    groups, i, n = [], 0, len(data)
    cur = None  # [start, end, strs]
    last_end = None
    while i < n:
        c = data[i]
        if c == 0x23:  # '#' 주석 -> 줄 끝까지
            j = data.find(b'\r\n', i)
            i = n if j < 0 else j
            continue
        if c == 0x22:  # '"'
            j = data.index(b'"', i + 1)
            s = data[i + 1:j]
            if cur is not None and data[last_end:i].strip() == b'':
                cur[2].append(s)
                cur[1] = j + 1
            else:
                if cur:
                    groups.append(cur)
                cur = [i, j + 1, [s]]
            last_end = j + 1
            i = j + 1
            continue
        if c not in b' \t\r\n' and cur is not None and last_end is not None and i >= last_end:
            groups.append(cur)
            cur = None
        i += 1
    if cur:
        groups.append(cur)
    return groups


def script_render(text: bytes, maxlen=70):
    """번역문을 maxlen 바이트 이하 따옴표 문자열 여러 개로 (공백 기준, 한글 2바이트는 안 쪼갬)."""
    words = text.split(b' ')
    lines, cur = [], b''
    for w in words:
        cand = w if not cur else cur + b' ' + w
        if len(cand) <= maxlen or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return b'\r\n\t\t\t'.join(b'"' + l + b'"' for l in lines)


# ---------------------------------------------------------------- 추출
def extract(dat, outdir):
    _, _, _, _, _, _, files = dat_load(dat)
    os.makedirs(outdir, exist_ok=True)
    total = 0
    for name in sorted(files):
        data = files[name]
        k = kind_of(name, data)
        if not k:
            continue
        items = []
        if k == 'ltx':
            for i, s in enumerate(ltx_items(data)):
                if s.strip():
                    items.append({'id': i, 'en': b2t(s), 'ko': ''})
        elif k == 'bintlk':
            p = bin_tlk_pos(data)
            for i, s in enumerate(data[p + 4:].split(b'\0')):
                if s.strip():
                    items.append({'id': i, 'en': b2t(s), 'ko': ''})
        else:
            for i, (a, b, strs) in enumerate(script_groups(data)):
                txt = b' '.join(strs)
                if txt.strip():
                    items.append({'id': i, 'en': b2t(txt), 'ko': ''})
        if items:
            total += len(items)
            json.dump({'file': name, 'kind': k, 'items': items},
                      open(os.path.join(outdir, name + '.json'), 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
    print('추출 완료: 항목', total)


# ---------------------------------------------------------------- 삽입
EMPTY = '<<EMPTY>>'  # 번역문을 빈 문자열로 만들고 싶을 때 (영어 복수형 's' 등)
_ph = re.compile(r'%[-+ #0]*\d*(?:\.\d+)?l?[sdicuxX]')


def check_item(en, ko):
    """번역문 점검: 서식 지정자 순서, 색상 코드 개수, 인코딩 가능 여부. 문제 목록 반환."""
    if not ko or ko == EMPTY:
        return []
    errs = []
    if _ph.findall(en) != _ph.findall(ko):
        errs.append('서식지정자 불일치 %s -> %s' % (_ph.findall(en), _ph.findall(ko)))
    for code in ('{F0}', '{F1}', '{F2}', '{F3}', '{F4}', '{F5}'):
        if en.count(code) != ko.count(code):
            errs.append('색상코드 %s 개수 다름' % code)
    try:
        t2b(ko)
    except ValueError as e:
        errs.append(str(e))
    return errs


def apply_file(name, data, table):
    k = table['kind']
    tr = {it['id']: ('' if it['ko'] == EMPTY else it['ko']) for it in table['items'] if it.get('ko')}
    if not tr:
        return data
    if k == 'ltx':
        parts = ltx_items(data)
        for i, t in tr.items():
            parts[i] = t2b(t)
        return ltx_build(parts)
    if k == 'bintlk':
        p = bin_tlk_pos(data)
        parts = data[p + 4:].split(b'\0')
        for i, t in tr.items():
            parts[i] = t2b(t)
        txt = b'\0'.join(parts)
        C = struct.unpack('<H', data[p + 2:p + 4])[0]
        return data[:p] + struct.pack('<HH', len(txt), C) + txt
    # script
    groups = script_groups(data)
    out, last = [], 0
    for i, (a, b, strs) in enumerate(groups):
        if i in tr:
            out.append(data[last:a])
            out.append(script_render(t2b(tr[i])))
            last = b
    out.append(data[last:])
    return b''.join(out)


def inject(dat, textdir, out_dat, extra=None):
    _, _, _, _, _, _, files = dat_load(dat)
    repl = dict(extra or {})
    for fn in sorted(os.listdir(textdir)):
        if not fn.endswith('.json'):
            continue
        table = json.load(open(os.path.join(textdir, fn), encoding='utf-8'))
        name = table['file']
        new = apply_file(name, repl.get(name, files[name]), table)
        if new != files[name]:
            repl[name] = new
    dat_save(dat, out_dat, repl)
    print('삽입 완료: 바뀐 파일', len(repl))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'extract':
        extract(sys.argv[2], sys.argv[3])
    elif cmd == 'inject':
        inject(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'check':
        n = done = 0
        for fn in sorted(os.listdir(sys.argv[2])):
            if not fn.endswith('.json'):
                continue
            t = json.load(open(os.path.join(sys.argv[2], fn), encoding='utf-8'))
            for it in t['items']:
                n += 1
                done += bool(it.get('ko'))
                for e in check_item(it['en'], it.get('ko')):
                    print('%s #%s: %s' % (t['file'], it['id'], e))
        print('번역 %d / %d 항목 (%.1f%%)' % (done, n, 100.0 * done / max(n, 1)))
    else:
        print('사용법: textdb.py extract STAR.DAT text_dir | inject STAR.DAT text_dir OUT.DAT')

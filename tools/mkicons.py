# -*- coding: utf-8 -*-
"""ICONS.NVF 상점 아이콘(HI/BUY/SELL) 말풍선을 한글로 다시 그림.
ICONS.NVF: [형식 0][개수 u16][폭 u16][높이 u16] + 24x24 원시 픽셀 * 72 + 팔레트"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mkfont import load_bdf  # noqa: E402

W = 24
WHITE, DARK, INK, YELLOW = 0xC8, 0xCC, 0xDD, 0xF9
# 아이콘 번호: (문구, 상자 x0, y0, x1, y1, 바탕색, 꼬리)
ICONS = {21: ('안녕!', 6, 9, 23, 19, WHITE, True),
         22: ('구입', 8, 10, 23, 19, WHITE, True),
         24: ('판매', 8, 11, 23, 19, YELLOW, False)}
BANG = (1, 1, 1, 1, 1, 0, 1)   # 느낌표 1x7


def glyph(bdf, ch):
    if ch == '!':
        return [[v] for v in BANG]
    g = bdf[ord(ch)]
    w, h, xo, yo = g['bbx']
    rows = [[0] * 7 for _ in range(7)]
    top = 7 - h - yo
    for y, r in enumerate(g['rows']):
        for x, v in enumerate(r):
            if v and 0 <= top + y < 7 and 0 <= xo + x < 7:
                rows[top + y][xo + x] = 1
    cols = [x for x in range(7) if any(rows[y][x] for y in range(7))]
    return [r[min(cols):max(cols) + 1] for r in rows]


def draw(icon, text, x0, y0, x1, y1, bg, tail, bdf):
    px = bytearray(icon)
    def put(x, y, c):
        if 0 <= x < W and 0 <= y < W:
            px[y * W + x] = c
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            corner = (x in (x0, x1)) and (y in (y0, y1))
            if corner:
                continue
            edge = x in (x0, x1) or y in (y0, y1)
            put(x, y, DARK if edge else bg)
    if tail:
        put(x0 - 1, y1, DARK); put(x0, y1, bg); put(x0 + 1, y1, bg)
    gl = [glyph(bdf, c) for c in text]
    tw = sum(len(g[0]) for g in gl) + len(gl) - 1
    x = x0 + 1 + (x1 - x0 - 1 - tw) // 2
    y = y0 + 1 + (y1 - y0 - 1 - 7) // 2
    for g in gl:
        for yy in range(7):
            for xx, v in enumerate(g[yy]):
                if v:
                    put(x + xx, y + yy, INK)
        x += len(g[0]) + 1
    return bytes(px)


def build_icons(nvf, bdf_path):
    bdf = load_bdf(bdf_path)
    d = bytearray(nvf)
    assert d[0] == 0 and d[3] == W and d[5] == W
    for i, (t, a, b, c, e, bg, tail) in ICONS.items():
        o = 7 + i * W * W
        d[o:o + W * W] = draw(d[o:o + W * W], t, a, b, c, e, bg, tail, bdf)
    return bytes(d)

# -*- coding: utf-8 -*-
"""번역 메모리: 영어 원문이 똑같은 항목은 이미 번역된 것을 그대로 채운다.
사용법: python3 tm.py text폴더"""
import json, os, sys
d = sys.argv[1]
tm, files = {}, []
for fn in sorted(os.listdir(d)):
    if fn.endswith('.json'):
        p = os.path.join(d, fn); t = json.load(open(p, encoding='utf-8')); files.append((p, t))
        for it in t['items']:
            if it.get('ko'):
                tm.setdefault(it['en'], it['ko'])
n = 0
for p, t in files:
    ch = False
    for it in t['items']:
        if not it.get('ko') and it['en'] in tm:
            it['ko'] = tm[it['en']]; n += 1; ch = True
    if ch:
        json.dump(t, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('번역 메모리로 채운 항목:', n)

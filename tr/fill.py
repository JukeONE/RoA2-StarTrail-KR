# 번역 입력 도우미: python3 fill.py 모듈명  (모듈 안의 FILE, T 딕셔너리를 text/FILE.json 의 ko 에 채움)
import json, os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'text')
def fill(fname, d):
    p = os.path.join(TEXT, fname + '.json'); t = json.load(open(p, encoding='utf-8'))
    ids = {it['id'] for it in t['items']}
    for k in d:
        if k not in ids: print('없는 id', fname, k)
    for it in t['items']:
        if it['id'] in d: it['ko'] = d[it['id']]
    json.dump(t, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
if __name__ == '__main__':
    for m in sys.argv[1:]:
        mod = importlib.import_module(m); fill(mod.FILE, mod.T); print('채움', mod.FILE, len(mod.T))

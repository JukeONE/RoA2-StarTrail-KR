import json,sys
for f in sys.argv[1:]:
  t=json.load(open('text/'+f+'.json')); print('=====',f)
  for i in t['items']:
    if not i['ko']: print(i['id'], i['en'])

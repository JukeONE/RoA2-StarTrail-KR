import struct,sys,os,collections
p=sys.argv[1]; d=open(p,'rb').read()
n=struct.unpack('<I',d[:4])[0]
ents=[]
for i in range(n):
    e=d[4+i*20:24+i*20]
    name=e[:14].split(b'\0')[0].decode('latin1'); off,fl=struct.unpack('<IH',e[14:20])
    ents.append((name,off,fl))
base=4+n*20-2
print('count',n,'base',base,'size',len(d))
offs=[e[1] for e in ents]
out=sys.argv[2]; os.makedirs(out,exist_ok=True)
ext=collections.Counter(); fl=collections.Counter(e[2] for e in ents)
srt=sorted(set(offs))+[len(d)-base]
for name,off,f in ents:
    if not name: continue
    i=srt.index(off); end=srt[i+1]
    open(os.path.join(out,name),'wb').write(d[base+off:base+end])
    ext[name.split('.')[-1]]+=1
print(ext); print('flags',fl)

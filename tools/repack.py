import struct,sys
def load(p):
    d=open(p,'rb').read(); n=struct.unpack('<I',d[:4])[0]; base=4+n*20-2
    ents=[]
    for i in range(n):
        e=d[4+i*20:24+i*20]; off=struct.unpack('<I',e[14:18])[0]; ents.append([e,off])
    return d,n,base,ents
def repack(src,dst,repl):
    d,n,base,ents=load(src)
    offs=sorted(set(o for _,o in ents)); ends=offs[1:]+[len(d)-base]
    blob={o:d[base+o:base+e] for o,e in zip(offs,ends)}
    for e,o in ents:
        nm=e[:14].split(b'\0')[0].decode()
        if nm in repl: blob[o]=repl[nm]
    newoff={}; cur=0; body=b''
    for o in offs: newoff[o]=cur; body+=blob[o]; cur+=len(blob[o])
    hdr=bytearray(d[:base])
    for i,(e,o) in enumerate(ents):
        struct.pack_into('<I',hdr,4+i*20+14,newoff[o])
    open(dst,'wb').write(bytes(hdr)+body)
if __name__=='__main__':
    repack(sys.argv[1],sys.argv[2],{})

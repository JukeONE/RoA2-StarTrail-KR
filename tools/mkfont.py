import struct
def load_bdf(p):
    g={};cur=None
    lines=open(p,encoding='latin1').read().splitlines();i=0
    while i<len(lines):
        l=lines[i]
        if l.startswith('ENCODING'): cur={'enc':int(l.split()[1])}
        elif l.startswith('DWIDTH') and cur is not None: cur['dw']=int(l.split()[1])
        elif l.startswith('BBX') and cur is not None: cur['bbx']=list(map(int,l.split()[1:]))
        elif l=='BITMAP':
            w,h,xo,yo=cur['bbx']; rows=[]
            for j in range(h):
                v=int(lines[i+1+j],16); nb=len(lines[i+1+j])*4
                rows.append([(v>>(nb-1-x))&1 for x in range(w)])
            cur['rows']=rows; g[cur['enc']]=cur; i+=h
        i+=1
    return g
CHARSET=" ABCDEFGHIJKLMNOPQRSTUVWXYZ\x8e\x99\x9a1234567890abcdefghijklmnopqrstuvwxyz\x84\x94\x81\xe1()!?:<>/_,.'-[];&"
def build(orig, H, replace):
    """replace: {ascii_char: hangul_char}"""
    n=87; dims=[struct.unpack('<HH',orig[3+i*4:7+i*4]) for i in range(n)]
    data=orig[3+4*n:]; p=0; glyphs=[]
    for w,h in dims:
        g8=[list(data[p+y*w:p+y*w+w]) for y in range(8)]; p+=w*8
        glyphs.append((w,[[0]*w]+g8+[[0]*w]*(H-9)))
    bdf=load_bdf('/home/claude/quiple/galmuri/dist/Galmuri9.bdf')
    for a,k in replace.items():
        b=bdf[ord(k)]; w,h,xo,yo=b['bbx']; W=9
        cell=[[0]*W for _ in range(H)]
        top=9-h-yo   # baseline at row 9 (rows 0..8 used)
        for y,row in enumerate(b['rows']):
            for x,v in enumerate(row):
                if v and 0<=top+y<H and 0<=xo+x<W: cell[top+y][xo+x]=1
        glyphs[CHARSET.index(a)]=(W,cell)
    out=bytearray(orig[:3]); px=bytearray()
    for w,rows in glyphs:
        out+=struct.pack('<HH',w,H)
        for r in rows: px+=bytes(r)
    return bytes(out+px+data[p:])

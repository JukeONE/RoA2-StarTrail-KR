import struct
UML={0x81,0x84,0x8E,0x94,0x99,0x9A,0xE1}
LEADS=[b for b in range(0x80,0xA8) if b not in UML]
TRAILS=[b for b in range(0xA8,0xF0) if b not in UML]
assert len(TRAILS)==71, len(TRAILS)
HANGUL=[bytes([a,b]).decode('euc-kr') for a in range(0xB0,0xC9) for b in range(0xA1,0xFF)]
assert len(HANGUL)==2350
IDX={c:i for i,c in enumerate(HANGUL)}
def enc(s):
    out=bytearray()
    for c in s:
        if c in IDX:
            k=IDX[c]; out+=bytes([LEADS[k//71],TRAILS[k%71]])
        else:
            o=ord(c)
            if o>=0x80: raise ValueError('unsupported char %r'%c)
            out.append(o)
    return bytes(out)

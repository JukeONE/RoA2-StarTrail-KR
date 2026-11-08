; replaces font-module bytes from seg offset 0x103 (DA83) to 0x195 (DB15)
BITS 16
ORG 0x103
BLOB  equ 4208
; ---- new DA83: char info -> blob hk_info
info:
        push bp
        mov bp,sp
        les bx,[bp+6]
        les bx,[es:bx+4]
        add bx,BLOB+0
        push cs
        push word .r
        push es
        push bx
        retf
.r:     pop bp
        retf

; ---- cave for DB1B (glyph ptr)
cave_db1b:
        push bp
        mov bp,sp
        mov al,[bp+0xa]
        cmp al,0xA8
        jb .orig
        cmp al,0xEF
        ja .orig
        les bx,[bp+6]
        les bx,[es:bx+4]
        add bx,BLOB+3
        push cs
        push word .r
        push es
        push bx
        retf
.r:     test dx,dx
        jz .orig
        pop bp
        retf
.orig:  sub sp,6
        jmp near 0x1A1          ; DB21

; ---- cave for DB79 (draw char): skip lead bytes (width==0xFFFF)
cave_db79:
        push bp
        mov bp,sp
        cmp word [bp+0xc],byte -1
        jne .go
        pop bp
        retf
.go:    sub sp,0xc
        jmp near 0x1FF          ; DB7F
end_:
%if (end_-info) > (0x196-0x103)
%error hook too large
%endif

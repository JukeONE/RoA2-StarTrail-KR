; Hangul extension blob appended to FONT.NVF. Position independent.
; Entry points at fixed offsets: 0 = hk_info, 3 = hk_glyph
BITS 16
ORG 0
NTRAIL equ 71
NGLYPH equ 2350
        jmp near hk_info        ; +0
        jmp near hk_glyph       ; +3

; ---------------- getbase: si = blob base ----------------
; stack frame (after push bp; mov bp,sp in routine):
; [bp+12] font far ptr, [bp+16] ch, [bp+18] wptr far (info only)

hk_info:
        push bp
        mov bp,sp
        push si
        push di
        push ds
        call .g
.g:     pop si
        sub si, .g
        push cs
        pop ds
        mov al,[bp+16]
        cmp al,0x80
        jb .orig
        cmp al,0xA7
        ja .trailchk
        ; lead byte
        movzx bx,al
        sub bx,0x80
        mov bl,[si+bx+leadtab]
        cmp bl,0xFF
        je .orig
        mov [si+st_lead],bl
        mov byte [si+st_have],1
        mov ax,0xFFFF
        xor dx,dx
        jmp .retw
.trailchk:
        cmp al,0xEF
        ja .orig
        cmp byte [si+st_have],0
        je .orig
        movzx bx,al
        sub bx,0xA8
        mov bl,[si+bx+trailtab]
        cmp bl,0xFF
        je .orig
        mov byte [si+st_have],0
        xor bh,bh
        movzx ax,byte [si+st_lead]
        mov dl,NTRAIL
        mul dl
        add ax,bx
        cmp ax,NGLYPH
        jae .orig
        mov [si+st_code],ax
        mov byte [si+st_cvalid],1
        mov ax,7
        xor dx,dx
        jmp .retw
.orig:
        mov byte [si+st_have],0
        mov byte [si+st_cvalid],0
        les bx,[bp+12]
        les bx,[es:bx+8]
        movzx di,byte [bp+16]
        shl di,2
        les bx,[es:bx+di]
        mov ax,es
        or ax,bx
        jz .noent
        movzx ax,byte [es:bx+3]
        mov dl,[es:bx+2]
        movsx dx,dl
        jmp .retw
.noent:
        mov cl,[bp+16]
        cmp cl,0x7E
        je .zero
        cmp cl,0xF0
        jb .five
        cmp cl,0xF5
        ja .five
.zero:  xor ax,ax
        xor dx,dx
        jmp .retw
.five:  mov ax,5
        xor dx,dx
.retw:  les bx,[bp+18]
        mov [es:bx],ax
        mov ax,dx
        pop ds
        pop di
        pop si
        pop bp
        retf

hk_glyph:
        push bp
        mov bp,sp
        push si
        push di
        push ds
        call .g
.g:     pop si
        sub si, .g
        push cs
        pop ds
        cmp byte [si+st_cvalid],0
        je .none
        mov ax,[si+st_code]
        cmp ax,NGLYPH
        jae .none
        shl ax,3
        lea bx,[si+glyphs]
        add bx,ax               ; bx -> 8 row bytes
        lea di,[si+gbuf]
        push cs
        pop es
        mov ch,8
.row:   mov dl,[bx]
        inc bx
        mov cl,7
.col:   xor al,al
        shl dl,1
        adc al,0
        stosb
        dec cl
        jnz .col
        dec ch
        jnz .row
        lea ax,[si+gbuf-1]
        mov dx,cs
        jmp .out
.none:  xor ax,ax
        xor dx,dx
.out:   pop ds
        pop di
        pop si
        pop bp
        retf

st_have   db 0
st_lead   db 0
st_cvalid db 0
          db 0
st_code   dw 0
leadtab:  times 40 db 0xFF      ; filled by builder (0x80..0xA7)
trailtab: times 72 db 0xFF      ; filled by builder (0xA8..0xEF)
gbuf:     times 56 db 0
glyphs:                          ; NGLYPH*8 bytes appended by builder

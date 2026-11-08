/* 한글패치 적용 핵심 코드 (Windows / 리눅스 공용, 리눅스에서 시험용으로도 빌드됨) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "core.h"

static uint32_t crc_tab[256];
static void crc_init(void) {
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t c = i;
        for (int k = 0; k < 8; k++) c = (c & 1) ? 0xEDB88320u ^ (c >> 1) : c >> 1;
        crc_tab[i] = c;
    }
}
uint32_t crc32_buf(const uint8_t *p, size_t n) {
    if (!crc_tab[1]) crc_init();
    uint32_t c = 0xFFFFFFFFu;
    while (n--) c = crc_tab[(c ^ *p++) & 0xFF] ^ (c >> 8);
    return c ^ 0xFFFFFFFFu;
}
static uint32_t rd32(const uint8_t *p) { return p[0] | p[1] << 8 | p[2] << 16 | (uint32_t)p[3] << 24; }
static void wr32(uint8_t *p, uint32_t v) { p[0] = v; p[1] = v >> 8; p[2] = v >> 16; p[3] = v >> 24; }

int patch_parse(const uint8_t *pl, size_t n, patch_t *pt) {
    if (n < 8 || memcmp(pl, "ROA2KR01", 8)) return 0;
    const uint8_t *p = pl + 8;
    pt->exe_size = rd32(p); pt->exe_crc = rd32(p + 4); pt->exe_n = rd32(p + 8); p += 12;
    pt->exe_parts = p;
    for (uint32_t i = 0; i < pt->exe_n; i++) p += 8 + rd32(p + 4);
    pt->dat_size = rd32(p); pt->dat_crc = rd32(p + 4); pt->dat_n = rd32(p + 8); p += 12;
    pt->dat_files = p;
    return 1;
}

int patch_exe(const patch_t *pt, uint8_t *exe, size_t n) {
    if (n != pt->exe_size || crc32_buf(exe, n) != pt->exe_crc) return 0;
    const uint8_t *p = pt->exe_parts;
    for (uint32_t i = 0; i < pt->exe_n; i++) {
        uint32_t off = rd32(p), len = rd32(p + 4);
        memcpy(exe + off, p + 8, len);
        p += 8 + len;
    }
    return 1;
}

static int cmp_u32(const void *a, const void *b) {
    uint32_t x = *(const uint32_t *)a, y = *(const uint32_t *)b;
    return x < y ? -1 : x > y;
}

/* STAR.DAT 다시 묶기: textdb.dat_save 와 같은 방식 */
uint8_t *patch_dat(const patch_t *pt, const uint8_t *d, size_t n, size_t *outn) {
    if (n != pt->dat_size || crc32_buf(d, n) != pt->dat_crc) return NULL;
    uint32_t cnt = rd32(d);
    size_t base = 4 + (size_t)cnt * 20 - 2;
    uint32_t *offs = malloc(cnt * 4);
    for (uint32_t i = 0; i < cnt; i++) offs[i] = rd32(d + 4 + i * 20 + 14);
    qsort(offs, cnt, 4, cmp_u32);
    uint32_t m = 0;
    for (uint32_t i = 0; i < cnt; i++) if (!m || offs[i] != offs[m - 1]) offs[m++] = offs[i];
    const uint8_t **bp = calloc(m, sizeof *bp);
    uint32_t *bl = calloc(m, 4), *noff = calloc(m, 4);
    for (uint32_t k = 0; k < m; k++) {
        uint32_t end = k + 1 < m ? offs[k + 1] : (uint32_t)(n - base);
        bp[k] = d + base + offs[k];
        bl[k] = end - offs[k];
    }
    /* 바뀐 파일 끼워 넣기 */
    const uint8_t *p = pt->dat_files;
    for (uint32_t f = 0; f < pt->dat_n; f++) {
        uint32_t len = rd32(p + 14);
        for (uint32_t i = 0; i < cnt; i++) {
            const uint8_t *e = d + 4 + i * 20;
            if (!strncmp((const char *)e, (const char *)p, 14)) {
                uint32_t o = rd32(e + 14);
                uint32_t *hit = bsearch(&o, offs, m, 4, cmp_u32);
                if (hit) { bp[hit - offs] = p + 18; bl[hit - offs] = len; }
                break;
            }
        }
        p += 18 + len;
    }
    size_t tot = base;
    for (uint32_t k = 0; k < m; k++) { noff[k] = (uint32_t)(tot - base); tot += bl[k]; }
    uint8_t *o = malloc(tot);
    memcpy(o, d, base);
    for (uint32_t i = 0; i < cnt; i++) {
        uint32_t old = rd32(d + 4 + i * 20 + 14);
        uint32_t *hit = bsearch(&old, offs, m, 4, cmp_u32);
        wr32(o + 4 + i * 20 + 14, noff[hit - offs]);
    }
    for (uint32_t k = 0; k < m; k++) memcpy(o + base + noff[k], bp[k], bl[k]);
    free(offs); free(bp); free(bl); free(noff);
    *outn = tot;
    return o;
}

#ifdef CORE_TEST
static uint8_t *slurp(const char *f, size_t *n) {
    FILE *fp = fopen(f, "rb"); if (!fp) return NULL;
    fseek(fp, 0, SEEK_END); *n = ftell(fp); fseek(fp, 0, SEEK_SET);
    uint8_t *b = malloc(*n); fread(b, 1, *n, fp); fclose(fp); return b;
}
int main(int c, char **v) {
    size_t pn, en, dn, on; patch_t pt;
    uint8_t *pl = slurp(v[1], &pn), *e = slurp(v[2], &en), *d = slurp(v[3], &dn);
    if (!patch_parse(pl, pn, &pt)) { puts("bad patch"); return 1; }
    if (!patch_exe(&pt, e, en)) { puts("bad exe"); return 1; }
    uint8_t *o = patch_dat(&pt, d, dn, &on);
    if (!o) { puts("bad dat"); return 1; }
    FILE *f = fopen(v[4], "wb"); fwrite(e, 1, en, f); fclose(f);
    f = fopen(v[5], "wb"); fwrite(o, 1, on, f); fclose(f);
    puts("ok"); return 0;
}
#endif

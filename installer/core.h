#pragma once
#include <stdint.h>
#include <stddef.h>
typedef struct {
    uint32_t exe_size, exe_crc, exe_n, dat_size, dat_crc, dat_n;
    const uint8_t *exe_parts, *dat_files;
} patch_t;
uint32_t crc32_buf(const uint8_t *p, size_t n);
int patch_parse(const uint8_t *pl, size_t n, patch_t *pt);
int patch_exe(const patch_t *pt, uint8_t *exe, size_t n);
uint8_t *patch_dat(const patch_t *pt, const uint8_t *d, size_t n, size_t *outn);

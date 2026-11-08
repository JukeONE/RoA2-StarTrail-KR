/* 아카니아 왕국 2: 스타 트레일 한글패치 설치 프로그램 (Win32) */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <commctrl.h>
#include <shlobj.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "core.h"

#define APP_TITLE L"아카니아 왕국 2: 스타 트레일 한글패치"
#define VERSION   L"v1.0"
#define CONF_NAME L"dosboxrealms2.conf"

enum { ID_PATH = 100, ID_BROWSE, ID_WIN, ID_FULL, ID_RES, ID_ASPECT, ID_SHADER, ID_INSTALL, ID_RESTORE, ID_CLOSE, ID_STATUS };

static HWND hMain, hPath, hWin, hFull, hRes, hAspect, hShader, hStatus;
static HFONT fNormal, fTitle, fSmall;
static uint8_t *payload; static size_t payload_n; static patch_t PT;

static const wchar_t *RES[] = { L"1280x800", L"1280x960", L"1440x900", L"1600x1000", L"1600x1200", L"1920x1080", L"1920x1200", L"960x600" };
static const struct { const wchar_t *label, *scaler; } SH[] = {
    { L"선명하게 (normal3x) - 글자가 가장 또렷함", L"normal3x" },
    { L"선명하게 2배 (normal2x)", L"normal2x" },
    { L"스캔라인 (scan3x) - 옛 모니터 가로줄", L"scan3x" },
    { L"TV 느낌 (tv3x)", L"tv3x" },
    { L"RGB 모니터 (rgb3x)", L"rgb3x" },
    { L"부드럽게 (hq3x)", L"hq3x" },
    { L"부드럽게 2 (advmame3x)", L"advmame3x" },
    { L"2xSaI (2xsai)", L"2xsai" },
};

/* ------------------------------------------------------------ 파일 도우미 */
static uint8_t *readall(const wchar_t *f, size_t *n) {
    FILE *fp = _wfopen(f, L"rb"); if (!fp) return NULL;
    fseek(fp, 0, SEEK_END); long l = ftell(fp); fseek(fp, 0, SEEK_SET);
    uint8_t *b = malloc(l ? l : 1); size_t r = fread(b, 1, l, fp); fclose(fp);
    if (r != (size_t)l) { free(b); return NULL; }
    *n = l; return b;
}
static int writeall(const wchar_t *f, const uint8_t *b, size_t n) {
    FILE *fp = _wfopen(f, L"wb"); if (!fp) return 0;
    size_t w = fwrite(b, 1, n, fp); fclose(fp); return w == n;
}
static int exists(const wchar_t *f) { return GetFileAttributesW(f) != INVALID_FILE_ATTRIBUTES; }
static void join(wchar_t *out, const wchar_t *dir, const wchar_t *name) { swprintf(out, MAX_PATH, L"%ls\\%ls", dir, name); }
static void status(const wchar_t *s) { SetWindowTextW(hStatus, s); UpdateWindow(hStatus); }

static int load_payload(void) {
    wchar_t me[MAX_PATH]; GetModuleFileNameW(NULL, me, MAX_PATH);
    size_t n; uint8_t *b = readall(me, &n);
    if (!b || n < 12 || memcmp(b + n - 8, "RKPAYLD!", 8)) return 0;
    uint32_t len = b[n - 12] | b[n - 11] << 8 | b[n - 10] << 16 | (uint32_t)b[n - 9] << 24;
    payload = b + n - 12 - len; payload_n = len;
    return patch_parse(payload, payload_n, &PT);
}

/* ------------------------------------------------------------ 게임 폴더 자동 찾기 */
static int is_game_dir(const wchar_t *d) {
    wchar_t a[MAX_PATH], b[MAX_PATH];
    join(a, d, L"STAR.EXE"); join(b, d, L"DATA\\STAR.DAT");
    return exists(a) && exists(b);
}
static int try_lib(const wchar_t *lib, wchar_t *out) {
    swprintf(out, MAX_PATH, L"%ls\\steamapps\\common\\Realms of Arkania 2 Startrail Classic", lib);
    return is_game_dir(out);
}
static int autodetect(wchar_t *out) {
    wchar_t steam[MAX_PATH]; DWORD sz = sizeof steam;
    if (RegGetValueW(HKEY_CURRENT_USER, L"Software\\Valve\\Steam", L"SteamPath", RRF_RT_REG_SZ, NULL, steam, &sz) != ERROR_SUCCESS) {
        sz = sizeof steam;
        if (RegGetValueW(HKEY_LOCAL_MACHINE, L"SOFTWARE\\WOW6432Node\\Valve\\Steam", L"InstallPath", RRF_RT_REG_SZ, NULL, steam, &sz) != ERROR_SUCCESS)
            return 0;
    }
    for (wchar_t *p = steam; *p; p++) if (*p == L'/') *p = L'\\';
    if (try_lib(steam, out)) return 1;
    /* 다른 라이브러리 폴더: libraryfolders.vdf 의 "path" 줄 */
    wchar_t vdf[MAX_PATH]; join(vdf, steam, L"steamapps\\libraryfolders.vdf");
    size_t n; uint8_t *b = readall(vdf, &n); if (!b) return 0;
    char *s = malloc(n + 1); memcpy(s, b, n); s[n] = 0; free(b);
    for (char *p = strstr(s, "\"path\""); p; p = strstr(p + 6, "\"path\"")) {
        char *q = strchr(p + 6, '"'); if (!q) break;
        char *e = strchr(q + 1, '"'); if (!e) break;
        char path[MAX_PATH * 2]; int k = 0;
        for (char *c = q + 1; c < e && k < (int)sizeof path - 1; c++) {
            if (c[0] == '\\' && c[1] == '\\') c++;
            path[k++] = *c;
        }
        path[k] = 0;
        wchar_t w[MAX_PATH]; MultiByteToWideChar(CP_UTF8, 0, path, -1, w, MAX_PATH);
        if (try_lib(w, out)) { free(s); return 1; }
    }
    free(s);
    return 0;
}

/* ------------------------------------------------------------ DOSBox 설정 */
static void conf_set(char **txt, size_t *len, const char *key, const char *val) {
    char *s = *txt; size_t kl = strlen(key);
    for (char *p = s; p && *p; ) {
        if ((p == s || p[-1] == '\n') && !strncmp(p, key, kl) && p[kl] == '=') {
            char *e = p + kl + 1; while (*e && *e != '\r' && *e != '\n') e++;
            size_t vl = strlen(val), oldl = e - (p + kl + 1);
            size_t pos = p - s;
            char *ns = malloc(*len - oldl + vl + 1);
            memcpy(ns, s, pos + kl + 1);
            memcpy(ns + pos + kl + 1, val, vl);
            memcpy(ns + pos + kl + 1 + vl, e, *len - (e - s) + 1);
            *len = *len - oldl + vl; free(s); *txt = ns; return;
        }
        p = strchr(p, '\n'); if (p) p++;
    }
}
static int write_conf(const wchar_t *dir, wchar_t *err) {
    wchar_t cf[MAX_PATH], bak[MAX_PATH];
    join(cf, dir, CONF_NAME); join(bak, dir, CONF_NAME L".bak");
    size_t n; uint8_t *b = readall(cf, &n);
    if (!b) { wcscpy(err, L"DOSBox 설정 파일(dosboxrealms2.conf)을 찾을 수 없습니다."); return 0; }
    if (!exists(bak)) writeall(bak, b, n);
    char *t = malloc(n + 1); memcpy(t, b, n); t[n] = 0; free(b);
    int full = SendMessageW(hFull, BM_GETCHECK, 0, 0) == BST_CHECKED;
    wchar_t wres[32]; GetWindowTextW(hRes, wres, 32);
    char res[32]; WideCharToMultiByte(CP_UTF8, 0, wres, -1, res, 32, NULL, NULL);
    int si = (int)SendMessageW(hShader, CB_GETCURSEL, 0, 0); if (si < 0) si = 0;
    char sc[32]; WideCharToMultiByte(CP_UTF8, 0, SH[si].scaler, -1, sc, 32, NULL, NULL);
    conf_set(&t, &n, "fullscreen", full ? "true" : "false");
    conf_set(&t, &n, "fullresolution", res);
    conf_set(&t, &n, "windowresolution", res);
    conf_set(&t, &n, "output", "ddraw");
    conf_set(&t, &n, "scaler", sc);
    conf_set(&t, &n, "aspect", SendMessageW(hAspect, BM_GETCHECK, 0, 0) == BST_CHECKED ? "true" : "false");
    int ok = writeall(cf, (uint8_t *)t, n); free(t);
    if (!ok) wcscpy(err, L"DOSBox 설정 파일을 쓸 수 없습니다.");
    return ok;
}

/* ------------------------------------------------------------ 설치 / 되돌리기 */
/* 원본 파일 고르기: 백업(STAR_ORIG)이 원본이면 그것, 아니면 현재 파일이 원본인지 확인 */
static uint8_t *load_orig(const wchar_t *cur, const wchar_t *bak, uint32_t size, uint32_t crc, size_t *n, int *need_backup) {
    uint8_t *b = readall(bak, n);
    if (b && *n == size && crc32_buf(b, *n) == crc) { *need_backup = 0; return b; }
    free(b);
    b = readall(cur, n);
    if (b && *n == size && crc32_buf(b, *n) == crc) { *need_backup = 1; return b; }
    free(b);
    return NULL;
}

static void do_install(void) {
    wchar_t dir[MAX_PATH], err[256] = L"";
    GetWindowTextW(hPath, dir, MAX_PATH);
    if (!is_game_dir(dir)) { MessageBoxW(hMain, L"게임 폴더가 아닙니다.\nSTAR.EXE 와 DATA\\STAR.DAT 가 있는 폴더를 골라 주세요.", APP_TITLE, MB_ICONWARNING); return; }
    wchar_t exe[MAX_PATH], exeb[MAX_PATH], dat[MAX_PATH], datb[MAX_PATH];
    join(exe, dir, L"STAR.EXE"); join(exeb, dir, L"STAR_ORIG.EXE");
    join(dat, dir, L"DATA\\STAR.DAT"); join(datb, dir, L"DATA\\STAR_ORIG.DAT");
    status(L"원본 파일 확인 중...");
    size_t en, dn, on; int be, bd;
    uint8_t *e = load_orig(exe, exeb, PT.exe_size, PT.exe_crc, &en, &be);
    uint8_t *d = e ? load_orig(dat, datb, PT.dat_size, PT.dat_crc, &dn, &bd) : NULL;
    if (!e || !d) {
        MessageBoxW(hMain, L"원본 게임 파일을 찾을 수 없습니다.\n\nSteam판 원본(STAR.EXE, DATA\\STAR.DAT)이 필요합니다.\n다른 패치가 적용돼 있다면 Steam에서 '게임 파일 무결성 확인'을 한 뒤 다시 시도해 주세요.", APP_TITLE, MB_ICONERROR);
        free(e); status(L""); return;
    }
    if (be && !writeall(exeb, e, en)) wcscpy(err, L"원본 STAR.EXE 백업 실패");
    if (!*err && bd && !writeall(datb, d, dn)) wcscpy(err, L"원본 STAR.DAT 백업 실패");
    status(L"한글패치 적용 중...");
    uint8_t *nd = NULL;
    if (!*err) {
        nd = patch_dat(&PT, d, dn, &on);
        if (!nd || !patch_exe(&PT, e, en)) wcscpy(err, L"패치 데이터 적용 실패");
    }
    if (!*err && !writeall(exe, e, en)) wcscpy(err, L"STAR.EXE 쓰기 실패 (게임이 켜져 있으면 끄고 다시 해 주세요)");
    if (!*err && !writeall(dat, nd, on)) wcscpy(err, L"STAR.DAT 쓰기 실패 (게임이 켜져 있으면 끄고 다시 해 주세요)");
    if (!*err) write_conf(dir, err);
    free(e); free(d); free(nd);
    if (*err) { status(L"실패"); MessageBoxW(hMain, err, APP_TITLE, MB_ICONERROR); return; }
    status(L"설치 완료!");
    MessageBoxW(hMain, L"한글패치를 설치했습니다.\nSteam에서 게임을 실행하세요.\n\n원본 파일은 STAR_ORIG.EXE, DATA\\STAR_ORIG.DAT 로 백업해 두었습니다.", APP_TITLE, MB_ICONINFORMATION);
}

static void do_restore(void) {
    wchar_t dir[MAX_PATH]; GetWindowTextW(hPath, dir, MAX_PATH);
    wchar_t exe[MAX_PATH], exeb[MAX_PATH], dat[MAX_PATH], datb[MAX_PATH], cf[MAX_PATH], cfb[MAX_PATH];
    join(exe, dir, L"STAR.EXE"); join(exeb, dir, L"STAR_ORIG.EXE");
    join(dat, dir, L"DATA\\STAR.DAT"); join(datb, dir, L"DATA\\STAR_ORIG.DAT");
    join(cf, dir, CONF_NAME); join(cfb, dir, CONF_NAME L".bak");
    if (!exists(exeb) || !exists(datb)) { MessageBoxW(hMain, L"백업된 원본 파일이 없습니다.\n(Steam의 '게임 파일 무결성 확인'으로도 원본을 되돌릴 수 있습니다.)", APP_TITLE, MB_ICONWARNING); return; }
    if (MessageBoxW(hMain, L"한글패치를 지우고 원본으로 되돌릴까요?", APP_TITLE, MB_YESNO | MB_ICONQUESTION) != IDYES) return;
    int ok = CopyFileW(exeb, exe, FALSE) && CopyFileW(datb, dat, FALSE);
    if (exists(cfb)) CopyFileW(cfb, cf, FALSE);
    status(ok ? L"원본으로 되돌렸습니다." : L"되돌리기 실패");
    MessageBoxW(hMain, ok ? L"원본으로 되돌렸습니다." : L"파일을 되돌리지 못했습니다. 게임이 켜져 있으면 끄고 다시 해 주세요.", APP_TITLE, ok ? MB_ICONINFORMATION : MB_ICONERROR);
}

static void browse(void) {
    BROWSEINFOW bi = { 0 };
    bi.hwndOwner = hMain; bi.lpszTitle = L"Realms of Arkania 2 Startrail Classic 게임 폴더를 골라 주세요";
    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE;
    LPITEMIDLIST id = SHBrowseForFolderW(&bi);
    if (id) {
        wchar_t p[MAX_PATH];
        if (SHGetPathFromIDListW(id, p)) SetWindowTextW(hPath, p);
        CoTaskMemFree(id);
    }
}

/* ------------------------------------------------------------ 창 */
static HWND mk(const wchar_t *cls, const wchar_t *txt, DWORD st, int x, int y, int w, int h, int id, HFONT f) {
    HWND c = CreateWindowExW(0, cls, txt, WS_CHILD | WS_VISIBLE | st, x, y, w, h, hMain, (HMENU)(INT_PTR)id, GetModuleHandleW(NULL), NULL);
    SendMessageW(c, WM_SETFONT, (WPARAM)f, TRUE);
    return c;
}

static LRESULT CALLBACK WndProc(HWND h, UINT m, WPARAM w, LPARAM l) {
    switch (m) {
    case WM_CREATE: {
        hMain = h;
        mk(L"STATIC", L"아카니아 왕국 2: 스타 트레일", 0, 20, 14, 420, 30, 0, fTitle);
        mk(L"STATIC", L"한글패치 " VERSION, 0, 22, 46, 200, 20, 0, fNormal);
        mk(L"STATIC", L"by.김쥬크", SS_RIGHT, 300, 46, 160, 20, 0, fNormal);
        mk(L"BUTTON", L"게임 폴더", BS_GROUPBOX, 14, 76, 452, 64, 0, fNormal);
        hPath = mk(L"EDIT", L"", WS_BORDER | ES_AUTOHSCROLL, 26, 102, 340, 24, ID_PATH, fSmall);
        mk(L"BUTTON", L"찾아보기", BS_PUSHBUTTON, 374, 101, 80, 26, ID_BROWSE, fNormal);
        mk(L"BUTTON", L"화면", BS_GROUPBOX, 14, 148, 452, 96, 0, fNormal);
        hWin = mk(L"BUTTON", L"창 모드", BS_AUTORADIOBUTTON | WS_GROUP, 28, 172, 100, 22, ID_WIN, fNormal);
        hFull = mk(L"BUTTON", L"전체화면", BS_AUTORADIOBUTTON, 132, 172, 100, 22, ID_FULL, fNormal);
        mk(L"STATIC", L"해상도", 0, 250, 175, 60, 20, 0, fNormal);
        hRes = mk(L"COMBOBOX", L"", CBS_DROPDOWNLIST | WS_VSCROLL, 312, 170, 140, 300, ID_RES, fNormal);
        hAspect = mk(L"BUTTON", L"4:3 화면비 유지 (그림이 납작해지지 않게)", BS_AUTOCHECKBOX, 28, 206, 400, 22, ID_ASPECT, fNormal);
        mk(L"BUTTON", L"그래픽 효과", BS_GROUPBOX, 14, 252, 452, 62, 0, fNormal);
        hShader = mk(L"COMBOBOX", L"", CBS_DROPDOWNLIST | WS_VSCROLL, 28, 276, 424, 300, ID_SHADER, fNormal);
        mk(L"BUTTON", L"한글패치 설치", BS_DEFPUSHBUTTON, 14, 328, 160, 36, ID_INSTALL, fNormal);
        mk(L"BUTTON", L"원본으로 되돌리기", BS_PUSHBUTTON, 182, 328, 160, 36, ID_RESTORE, fNormal);
        mk(L"BUTTON", L"닫기", BS_PUSHBUTTON, 350, 328, 116, 36, ID_CLOSE, fNormal);
        hStatus = mk(L"STATIC", L"", 0, 16, 374, 450, 20, ID_STATUS, fSmall);
        for (size_t i = 0; i < sizeof RES / sizeof *RES; i++) SendMessageW(hRes, CB_ADDSTRING, 0, (LPARAM)RES[i]);
        for (size_t i = 0; i < sizeof SH / sizeof *SH; i++) SendMessageW(hShader, CB_ADDSTRING, 0, (LPARAM)SH[i].label);
        SendMessageW(hRes, CB_SETCURSEL, 0, 0);
        SendMessageW(hShader, CB_SETCURSEL, 0, 0);
        SendMessageW(hWin, BM_SETCHECK, BST_CHECKED, 0);
        SendMessageW(hAspect, BM_SETCHECK, BST_CHECKED, 0);
        wchar_t g[MAX_PATH];
        if (autodetect(g)) { SetWindowTextW(hPath, g); status(L"Steam 게임 폴더를 찾았습니다."); }
        else status(L"게임 폴더를 골라 주세요.");
        if (!payload_n) { status(L"패치 데이터가 없습니다 (설치 파일이 손상됨)"); EnableWindow(GetDlgItem(h, ID_INSTALL), FALSE); }
        return 0; }
    case WM_CTLCOLORSTATIC: SetBkMode((HDC)w, TRANSPARENT); return (LRESULT)GetSysColorBrush(COLOR_BTNFACE);
    case WM_COMMAND:
        switch (LOWORD(w)) {
        case ID_BROWSE: browse(); break;
        case ID_INSTALL: do_install(); break;
        case ID_RESTORE: do_restore(); break;
        case ID_CLOSE: DestroyWindow(h); break;
        }
        return 0;
    case WM_DESTROY: PostQuitMessage(0); return 0;
    }
    return DefWindowProcW(h, m, w, l);
}

int WINAPI wWinMain(HINSTANCE hi, HINSTANCE hp, PWSTR cmd, int show) {
    (void)hp; (void)cmd;
    INITCOMMONCONTROLSEX ic = { sizeof ic, ICC_STANDARD_CLASSES };
    InitCommonControlsEx(&ic);
    CoInitialize(NULL);
    load_payload();
    fNormal = CreateFontW(-15, 0, 0, 0, FW_NORMAL, 0, 0, 0, HANGUL_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, L"맑은 고딕");
    fSmall = CreateFontW(-13, 0, 0, 0, FW_NORMAL, 0, 0, 0, HANGUL_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, L"맑은 고딕");
    fTitle = CreateFontW(-24, 0, 0, 0, FW_BOLD, 0, 0, 0, HANGUL_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, L"맑은 고딕");
    WNDCLASSW wc = { 0 };
    wc.lpfnWndProc = WndProc; wc.hInstance = hi; wc.lpszClassName = L"ROA2KR";
    wc.hCursor = LoadCursor(NULL, IDC_ARROW); wc.hbrBackground = GetSysColorBrush(COLOR_BTNFACE);
    wc.hIcon = LoadIconW(hi, MAKEINTRESOURCEW(1));
    RegisterClassW(&wc);
    RECT r = { 0, 0, 480, 400 };
    DWORD st = WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX;
    AdjustWindowRect(&r, st, FALSE);
    HWND h = CreateWindowW(L"ROA2KR", APP_TITLE L" " VERSION L" - by.김쥬크", st, CW_USEDEFAULT, CW_USEDEFAULT, r.right - r.left, r.bottom - r.top, NULL, NULL, hi, NULL);
    ShowWindow(h, show); UpdateWindow(h);
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        if (!IsDialogMessageW(h, &msg)) { TranslateMessage(&msg); DispatchMessageW(&msg); }
    }
    return 0;
}

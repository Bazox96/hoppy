"""Foto di una finestra in PNG (solo stdlib: GDI via ctypes + zlib), da mandare a Claude."""
import ctypes
import ctypes.wintypes as wt
import struct
import zlib

MAX_SIDE = 1568             # Claude ridimensiona comunque oltre questo lato: inutile mandare di più

user32 = ctypes.WinDLL("user32")
gdi32 = ctypes.WinDLL("gdi32")
dwmapi = ctypes.WinDLL("dwmapi")
for f, args in ((user32.GetWindowDC, [wt.HWND]), (user32.ReleaseDC, [wt.HWND, wt.HDC]),
                (user32.PrintWindow, [wt.HWND, wt.HDC, wt.UINT]),
                (user32.GetWindowRect, [wt.HWND, ctypes.POINTER(wt.RECT)]),
                (user32.IsIconic, [wt.HWND]), (user32.IsWindow, [wt.HWND]),
                (gdi32.CreateCompatibleDC, [wt.HDC]), (gdi32.DeleteDC, [wt.HDC]),
                (gdi32.CreateCompatibleBitmap, [wt.HDC, ctypes.c_int, ctypes.c_int]),
                (gdi32.SelectObject, [wt.HDC, wt.HGDIOBJ]), (gdi32.DeleteObject, [wt.HGDIOBJ]),
                (gdi32.SetStretchBltMode, [wt.HDC, ctypes.c_int]),
                (gdi32.StretchBlt, [wt.HDC] + [ctypes.c_int] * 4 + [wt.HDC] + [ctypes.c_int] * 4
                 + [wt.DWORD]),
                (gdi32.GetDIBits, [wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT, ctypes.c_void_p,
                                   ctypes.c_void_p, wt.UINT])):
    f.argtypes = args
user32.GetWindowDC.restype = wt.HDC
gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.CreateCompatibleBitmap.restype = wt.HBITMAP
gdi32.SelectObject.restype = wt.HGDIOBJ

PW_RENDERFULLCONTENT = 2    # anche Chrome, Edge e le app moderne, coperte o no
SRCCOPY, HALFTONE = 0x00CC0020, 4
DWMWA_EXTENDED_FRAME_BOUNDS = 9


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def png(w, h, bgra):
    """PNG RGB da pixel BGRA dall'alto in basso."""
    rgb = bytearray(w * h * 3)
    rgb[0::3], rgb[1::3], rgb[2::3] = bgra[2::4], bgra[1::4], bgra[0::4]
    stride = w * 3
    raw = b"".join(b"\0" + rgb[y * stride:(y + 1) * stride] for y in range(h))

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def capture(hwnd):
    """PNG della finestra (anche se coperta), rimpicciolita a MAX_SIDE; None se non si può."""
    if not hwnd or not user32.IsWindow(hwnd) or user32.IsIconic(hwnd):
        return None
    win = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(win))
    vis = wt.RECT()                          # senza l'ombra invisibile ai lati
    if dwmapi.DwmGetWindowAttribute(wt.HWND(hwnd), DWMWA_EXTENDED_FRAME_BOUNDS,
                                    ctypes.byref(vis), ctypes.sizeof(vis)) != 0:
        vis = win
    W, H = win.right - win.left, win.bottom - win.top
    cx, cy = vis.left - win.left, vis.top - win.top
    cw, ch = vis.right - vis.left, vis.bottom - vis.top
    if cw < 8 or ch < 8:
        return None
    k = min(1.0, MAX_SIDE / max(cw, ch))
    w, h = max(1, int(cw * k)), max(1, int(ch * k))
    wdc = user32.GetWindowDC(hwnd)
    full_dc, small_dc = gdi32.CreateCompatibleDC(wdc), gdi32.CreateCompatibleDC(wdc)
    full, small = gdi32.CreateCompatibleBitmap(wdc, W, H), gdi32.CreateCompatibleBitmap(wdc, w, h)
    old_f, old_s = gdi32.SelectObject(full_dc, full), gdi32.SelectObject(small_dc, small)
    try:
        if not user32.PrintWindow(hwnd, full_dc, PW_RENDERFULLCONTENT):
            return None
        gdi32.SetStretchBltMode(small_dc, HALFTONE)
        gdi32.StretchBlt(small_dc, 0, 0, w, h, full_dc, cx, cy, cw, ch, SRCCOPY)
        bi = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32, 0)   # -h: dall'alto
        buf = ctypes.create_string_buffer(w * h * 4)
        if not gdi32.GetDIBits(small_dc, small, 0, h, buf, ctypes.byref(bi), 0):
            return None
        return png(w, h, buf.raw)
    finally:
        gdi32.SelectObject(full_dc, old_f)
        gdi32.SelectObject(small_dc, old_s)
        for b in (full, small):
            gdi32.DeleteObject(b)
        gdi32.DeleteDC(full_dc)
        gdi32.DeleteDC(small_dc)
        user32.ReleaseDC(hwnd, wdc)

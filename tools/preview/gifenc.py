"""GIF animata da fotogrammi BGRA (solo stdlib): palette globale da 256 colori, ogni
fotogramma salva solo il rettangolo cambiato rispetto al precedente, compressione LZW."""
import struct
from collections import Counter


def _palette(frames, w):
    cnt = Counter()
    for f in frames[::5]:
        cnt.update(f[i:i + 3] for i in range(0, len(f), 4 * 3))   # un pixel ogni 3
    pal = [c for c, _ in cnt.most_common(256)]
    return pal + [b"\0\0\0"] * (256 - len(pal))


def _nearest(c, pal_rgb):
    b, g, r = c
    return min(range(len(pal_rgb)), key=lambda i: (pal_rgb[i][0] - r) ** 2 * 3
               + (pal_rgb[i][1] - g) ** 2 * 4 + (pal_rgb[i][2] - b) ** 2 * 2)


def _first_diff(a, b):
    lo, hi = 0, len(a)
    if a == b:
        return None
    while hi - lo > 1:                        # ricerca binaria sul primo byte diverso
        mid = (lo + hi) // 2
        if a[lo:mid] != b[lo:mid]:
            hi = mid
        else:
            lo = mid
    return lo


def _bbox(prev, cur, w, h):
    stride = w * 4
    rows = [y for y in range(h) if prev[y * stride:(y + 1) * stride] != cur[y * stride:(y + 1) * stride]]
    if not rows:
        return 0, 0, 1, 1
    x0, x1 = w, 0
    for y in rows:
        a, b = prev[y * stride:(y + 1) * stride], cur[y * stride:(y + 1) * stride]
        x0 = min(x0, _first_diff(a, b) // 4)
        x1 = max(x1, w - _first_diff(a[::-1], b[::-1]) // 4)
    return x0, rows[0], max(x1, x0 + 1), rows[-1] + 1


def _lzw(indices):
    clear, eoi, size = 256, 257, 9
    table = {bytes([i]): i for i in range(256)}
    nxt = 258
    out, bits, nbits = bytearray(), 0, 0

    def emit(code):
        nonlocal bits, nbits
        bits |= code << nbits
        nbits += size
        while nbits >= 8:
            out.append(bits & 0xFF)
            bits >>= 8
            nbits -= 8
    emit(clear)
    cur = b""
    for i in indices:
        nxt_s = cur + bytes([i])
        if nxt_s in table:
            cur = nxt_s
            continue
        emit(table[cur])
        if nxt < 4096:
            table[nxt_s] = nxt
            if nxt == (1 << size) and size < 12:
                size += 1
            nxt += 1
        else:
            emit(clear)
            table = {bytes([k]): k for k in range(256)}
            nxt, size = 258, 9
        cur = bytes([i])
    if cur:
        emit(table[cur])
    emit(eoi)
    if nbits:
        out.append(bits & 0xFF)
    return bytes(out)


def write(path, w, h, frames, delay_cs=10, last_cs=None):
    pal = _palette(frames, w)
    pal_rgb = [(c[2], c[1], c[0]) for c in pal]
    index = {c: i for i, c in enumerate(pal)}
    data = bytearray(b"GIF89a" + struct.pack("<HHBBB", w, h, 0xF7, 0, 0))
    data += b"".join(bytes(rgb) for rgb in pal_rgb)
    data += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"           # ripeti all'infinito
    prev = None
    for n, f in enumerate(frames):
        x0, y0, x1, y1 = (0, 0, w, h) if prev is None else _bbox(prev, f, w, h)
        prev = f
        idx = bytearray()
        for y in range(y0, y1):
            row = f[(y * w + x0) * 4:(y * w + x1) * 4]
            for i in range(0, len(row), 4):
                c = row[i:i + 3]
                k = index.get(c)
                if k is None:
                    k = index[c] = _nearest(c, pal_rgb)
                idx.append(k)
        data += b"\x21\xF9\x04\x04" + struct.pack("<H", last_cs if last_cs and n == len(frames) - 1 else delay_cs) + b"\x00\x00"
        data += b"\x2C" + struct.pack("<HHHHB", x0, y0, x1 - x0, y1 - y0, 0) + b"\x08"
        lz = _lzw(idx)
        for i in range(0, len(lz), 255):
            data += bytes([len(lz[i:i + 255])]) + lz[i:i + 255]
        data += b"\x00"
    data += b"\x3B"
    path.write_bytes(bytes(data))

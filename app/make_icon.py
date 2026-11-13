#!/usr/bin/env python3
# ============================================================
#  Marshall CODE · Gateway Web — icon generator
#  ------------------------------------------------------------
#  Writes icon.png (256×256 RGBA) and icon.ico (multi-size,
#  PNG-compressed) next to the project root, using only the
#  Python standard library — no Pillow, no image libraries.
#
#  Called automatically by build.py when the icons are missing;
#  can also be run by hand:
#      python3 app/make_icon.py
# ============================================================

import math
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# --- palette (matches the app theme) --------------------------------------
BG_TOP = (35, 32, 27)        # #23201b
BG_BOTTOM = (18, 17, 16)     # #121110
BRASS = (201, 162, 75)       # #c9a24b
BRASS_HI = (221, 187, 111)   # #ddbb6f
BRASS_LO = (176, 138, 63)    # #b08a3f
DARK = (23, 22, 19)          # #171613


# ---------------------------------------------------------------
#  PNG / ICO containers
# ---------------------------------------------------------------
def _png(width, height, rgba):
    """Encode raw RGBA bytes (row-major, 4 Bpp) as a PNG."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))

    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)                      # filter: none
        raw += rgba[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def _ico(entries):
    """Build an .ico from [(size, png_bytes), ...] (PNG-compressed entries)."""
    header = struct.pack("<HHH", 0, 1, len(entries))
    offset = 6 + 16 * len(entries)
    directory = b""
    blob = b""
    for size, png in entries:
        dim = 0 if size >= 256 else size          # 0 means 256 in the ICO format
        directory += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        offset += len(png)
        blob += png
    return header + directory + blob


# ---------------------------------------------------------------
#  Shape tests (normalised 0..1 coordinates)
# ---------------------------------------------------------------
def _round_rect(u, v, pad, radius):
    hx = 0.5 - pad
    qx = abs(u - 0.5) - (hx - radius)
    qy = abs(v - 0.5) - (hx - radius)
    d = math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - radius
    return d <= 0.0


def _circle(u, v, cx, cy, r):
    return (u - cx) ** 2 + (v - cy) ** 2 <= r * r


# The "M" glyph, as fractions of a box (x0..x1, y0..y1).
_M_BOX = (0.300, 0.700, 0.372, 0.628)
_M_PTS = [
    (0.00, 1.00), (0.00, 0.00), (0.30, 0.00), (0.50, 0.52),
    (0.70, 0.00), (1.00, 0.00), (1.00, 1.00), (0.76, 1.00),
    (0.76, 0.40), (0.55, 1.00), (0.45, 1.00), (0.24, 0.40),
    (0.24, 1.00),
]


def _point_in_poly(u, v, pts):
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > v) != (yj > v):
            if u < (xj - xi) * (v - yi) / (yj - yi) + xi:
                inside = not inside
        j = i
    return inside


def _in_m(u, v):
    x0, x1, y0, y1 = _M_BOX
    if not (x0 <= u <= x1 and y0 <= v <= y1):
        return False
    return _point_in_poly((u - x0) / (x1 - x0), (v - y0) / (y1 - y0), _M_PTS)


def _lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------
#  Renderer
# ---------------------------------------------------------------
def _shade(u, v):
    """Return (r, g, b, a) for one sample."""
    if not _round_rect(u, v, 0.020, 0.215):
        return (0, 0, 0, 0)
    col = _lerp(BG_TOP, BG_BOTTOM, v)                       # background
    if _round_rect(u, v, 0.055, 0.180) and not _round_rect(u, v, 0.086, 0.150):
        col = BRASS                                          # bezel ring
    if _circle(u, v, 0.5, 0.5, 0.335):                       # knob face
        col = _lerp(BRASS_HI, BRASS_LO, (v - 0.165) / 0.67)
    if _in_m(u, v):                                          # logo
        col = DARK
    return (col[0], col[1], col[2], 255)


def render(size, ss=4):
    """Render one size with ss× supersampling, box-filtered down."""
    grid = size * ss
    n = grid * grid
    r_acc = [0] * n
    g_acc = [0] * n
    b_acc = [0] * n
    a_acc = [0] * n
    for iy in range(grid):
        v = (iy + 0.5) / grid
        base = iy * grid
        for ix in range(grid):
            u = (ix + 0.5) / grid
            r, g, b, a = _shade(u, v)
            k = base + ix
            r_acc[k] = r
            g_acc[k] = g
            b_acc[k] = b
            a_acc[k] = a

    out = bytearray(size * size * 4)
    inv = 1.0 / (ss * ss)
    for y in range(size):
        for x in range(size):
            rs = gs = bs = as_ = 0
            for dy in range(ss):
                row = (y * ss + dy) * grid + x * ss
                for dx in range(ss):
                    k = row + dx
                    a = a_acc[k]
                    # premultiply so transparent samples don't darken edges
                    rs += r_acc[k] * a
                    gs += g_acc[k] * a
                    bs += b_acc[k] * a
                    as_ += a
            if as_ > 0:
                r = rs / as_
                g = gs / as_
                b = bs / as_
            else:
                r = g = b = 0
            o = (y * size + x) * 4
            out[o] = int(r + 0.5)
            out[o + 1] = int(g + 0.5)
            out[o + 2] = int(b + 0.5)
            out[o + 3] = int(as_ * inv + 0.5)
    return bytes(out)


def main():
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    entries = []
    for s in ico_sizes:
        entries.append((s, _png(s, s, render(s))))

    png_path = os.path.join(ROOT, "icon.png")
    ico_path = os.path.join(ROOT, "icon.ico")
    with open(png_path, "wb") as f:
        f.write(_png(256, 256, render(256)))
    with open(ico_path, "wb") as f:
        f.write(_ico(entries))
    print("Wrote %s and %s" % (png_path, ico_path))
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(main())
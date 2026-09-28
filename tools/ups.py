"""Minimal UPS patch creator/applier.  ups.py make SRC DST OUT.ups | ups.py apply SRC PATCH OUT"""
import sys, zlib


def _enc(n):
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def _dec(buf, i):
    n, shift = 0, 1
    while True:
        x = buf[i]; i += 1
        n += (x & 0x7F) * shift
        if x & 0x80:
            return n, i
        shift <<= 7
        n += shift


def make(src, dst):
    out = bytearray(b"UPS1") + _enc(len(src)) + _enc(len(dst))
    n = max(len(src), len(dst))
    s = src + bytes(n - len(src))
    i = last = 0
    while i < len(dst):
        if s[i] == dst[i]:
            i += 1
            continue
        out += _enc(i - last)
        while i < len(dst) and s[i] != dst[i]:
            out.append(s[i] ^ dst[i]); i += 1
        out.append(0)
        i += 1
        last = i
    out += zlib.crc32(src).to_bytes(4, "little") + zlib.crc32(dst).to_bytes(4, "little")
    out += zlib.crc32(bytes(out)).to_bytes(4, "little")
    return bytes(out)


def apply(src, patch):
    assert patch[:4] == b"UPS1"
    i = 4
    ss, i = _dec(patch, i)
    ts, i = _dec(patch, i)
    assert zlib.crc32(src) == int.from_bytes(patch[-12:-8], "little"), "source ROM checksum mismatch"
    out = bytearray(src[:ts] + bytes(max(0, ts - len(src))))
    pos = 0
    end = len(patch) - 12
    while i < end:
        skip, i = _dec(patch, i)
        pos += skip
        while patch[i]:
            out[pos] ^= patch[i]; pos += 1; i += 1
        i += 1; pos += 1
    assert zlib.crc32(bytes(out)) == int.from_bytes(patch[-8:-4], "little"), "result checksum mismatch"
    return bytes(out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    a = open(sys.argv[2], "rb").read(); b = open(sys.argv[3], "rb").read()
    if cmd == "make":
        p = make(a, b); open(sys.argv[4], "wb").write(p)
        assert apply(a, p) == b
        print("wrote %s (%d bytes), verified" % (sys.argv[4], len(p)))
    else:
        open(sys.argv[4], "wb").write(apply(a, b)); print("patched ->", sys.argv[4])

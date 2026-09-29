"""Check that the ROMs are the clean US versions the build expects (a wrong ROM builds a broken game)."""
import sys, zlib

EXPECTED = {
    "FE8": ("A47246AE", "Fire Emblem: The Sacred Stones (USA)"),
    "FE7": ("2A524221", "Fire Emblem (USA), the GBA game also called Blazing Blade"),
}


def crc(path):
    with open(path, "rb") as f:
        return "%08X" % (zlib.crc32(f.read()) & 0xFFFFFFFF)


bad = False
for (key, (want, title)), path in zip(EXPECTED.items(), sys.argv[1:3]):
    got = crc(path)
    if got != want:
        bad = True
        print("checkroms: %s has CRC32 %s, but a clean %s has %s." % (path, got, title, want))
        print("           Use an unmodified, unpatched USA dump (not a Europe/Japan version or an already-patched ROM).")
if bad:
    sys.exit(1)

"""Mirror Blade & Stone sources into the engine tree (copy only what changed, so make stays incremental).

  overlay/**      -> engine/**                              (our edits to engine files)
  gen/engine/**   -> engine/**                              (generated engine tables)
  src/**          -> engine/Contents/BladeAndStone/**       (our content)
  gen/**          -> engine/Contents/BladeAndStone/gen/**   (generated content, minus gen/engine)
"""
import filecmp, os, shutil, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
ENGINE = os.path.join(ROOT, "engine")
DEST = os.path.join(ENGINE, "Contents", "BladeAndStone")


def mirror(src, dst, skip=()):
    n = 0
    for dp, dns, fns in os.walk(src):
        rel = os.path.relpath(dp, src)
        if any(rel == s or rel.startswith(s + os.sep) for s in skip):
            continue
        for fn in fns:
            a = os.path.join(dp, fn)
            b = os.path.normpath(os.path.join(dst, rel, fn))
            if os.path.exists(b) and filecmp.cmp(a, b, shallow=False):
                continue
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copy2(a, b)
            os.utime(b)            # newer than make's outputs
            n += 1
    return n


if __name__ == "__main__":
    n = mirror(os.path.join(ROOT, "overlay"), ENGINE)
    n += mirror(os.path.join(ROOT, "gen", "engine"), ENGINE)
    n += mirror(os.path.join(ROOT, "src"), DEST)
    n += mirror(os.path.join(ROOT, "gen"), os.path.join(DEST, "gen"), skip=("engine",))
    print("sync: %d file(s) updated in engine/" % n)

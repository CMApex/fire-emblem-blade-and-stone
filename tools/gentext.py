"""Compile Blade & Stone text together with the C-SkillSys kernel/vanilla text.

Why this exists instead of the engine's own Contents/Texts makefile rule:
  * our messages must be appended to the one global text table (IDs after the kernel's),
  * but the kernel's generated msgs.h is included by ~50 C files, so rewriting it on every
    script edit would recompile half the kernel. We therefore write msgs.h only when the
    kernel part actually changes, and put our BS_* IDs in gen/BsMsgs.event for EA.
  * the engine's text parser silently drops unknown [codes], treats // comments badly and
    crashes on messages without a terminator; we pre-clean our files and fail loudly.

Usage: python3 tools/gentext.py            (run by build.sh)
"""
import os, re, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
ENGINE = os.path.join(ROOT, "engine")
TEXTS = os.path.join(ENGINE, "Contents", "Texts")
GEN = os.path.join(ROOT, "gen")
SRC_ROOT = os.path.join(ROOT, "src", "Text", "blade.txt")

sys.path.insert(0, os.path.join(TEXTS, "Scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location("tp", os.path.join(TEXTS, "Scripts", "textprocess-chax.py"))
tp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tp)
tp.MSG_LENGTH = 0x2000                   # AllocMsgTable reserves 0x2000 entries
tp.msg_refs = [-1] * tp.MSG_LENGTH

RE_DEF = re.compile(r'^\[(.*?)\]\s*=\s*(.+)$')
RE_CODE = re.compile(r'\[(.*?)\]')


def load_kernel_defs():
    d = {}
    for line in open(os.path.join(TEXTS, "textdefs.txt"), encoding="utf-8"):
        m = RE_DEF.match(line.strip())
        if m:
            d[m.group(1)] = [int(v.strip(), 0) for v in m.group(2).split(",")]
    return d


def load_alias_defs(paths, kernel):
    """Our alias files use the old-buildfile style: [Name] = [Other][0x12]..."""
    alias = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            m = RE_DEF.match(line)
            if m:
                alias[m.group(1)] = m.group(2)
    return alias


def expand(code, kernel, alias, depth=0):
    """Return the list of byte values for one [code]."""
    if depth > 16:
        raise ValueError("alias loop at [%s]" % code)
    if re.fullmatch(r'0[xX][0-9a-fA-F]{1,2}', code):
        return [int(code, 16)]
    if code in kernel:
        return kernel[code]
    if code in alias:
        out = []
        rhs = alias[code]
        pos = 0
        for m in RE_CODE.finditer(rhs):
            lit = rhs[pos:m.start()]
            out += list(lit.encode("utf-8"))
            out += expand(m.group(1), kernel, alias, depth + 1)
            pos = m.end()
        out += list(rhs[pos:].encode("utf-8"))
        return out
    raise KeyError(code)


def read_messages(path, seen=None):
    """Parse our text files: '## NAME' headers, bodies until the next header; // comments stripped."""
    seen = seen if seen is not None else set()
    path = os.path.normpath(path)
    if path in seen:
        raise ValueError("recursive include " + path)
    seen.add(path)
    msgs = []
    cur = None
    pending_allow = False
    for ln, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        s = line.strip()
        m = re.match(r'#include\s+"([^"]+)"', s)
        if m:
            cur = None
            msgs += read_messages(os.path.join(os.path.dirname(path), m.group(1)), seen)
            continue
        if s.startswith("//"):
            if "allow-4-faces" in s:
                pending_allow = True
            continue
        if not s and cur is None:
            continue
        m = re.match(r'^##\s*(\w+)\s*$', s)
        if m:
            cur = [m.group(1), [], path, ln, pending_allow]
            pending_allow = False
            msgs.append(cur)
            continue
        if s.startswith("#"):
            raise SyntaxError("%s:%d: unexpected directive %r" % (path, ln, s))
        if cur is None:
            if s:
                raise SyntaxError("%s:%d: text outside of a message" % (path, ln))
            continue
        # strip trailing // comments only when they follow a closing code (never inside prose)
        cur[1].append(line.rstrip())
    return msgs


def encode_body(name, body, kernel, alias, where):
    text = "".join(body)
    out = bytearray()
    pos = 0
    for m in RE_CODE.finditer(text):
        out += text[pos:m.start()].encode("utf-8")
        try:
            out += bytes(expand(m.group(1), kernel, alias))
        except KeyError:
            raise SyntaxError("%s: message %s uses unknown code [%s]" % (where, name, m.group(1)))
        pos = m.end()
    tail = text[pos:]
    if tail.strip():
        raise SyntaxError("%s: message %s has text after its last code (missing [X]?): %r" % (where, name, tail[:40]))
    if not out or out[-1] != 0:
        raise SyntaxError("%s: message %s must end with [X]" % (where, name))
    return bytes(out)


def max_faces(data):
    """Most portraits on screen at once. 0x08-0x0F select a position, 0x10 xx xx loads a face there,
    0x11 clears it."""
    pos, faces, most, i = None, set(), 0, 0
    while i < len(data):
        b = data[i]
        if 0x08 <= b <= 0x0F:
            pos = b
        elif b == 0x10 and i + 2 < len(data):
            faces.add(pos); most = max(most, len(faces)); i += 2
        elif b == 0x11:
            faces.discard(pos)
        elif b == 0x80 and i + 1 < len(data):
            i += 1
        i += 1
    return most


def to_clean_line(data):
    """Re-emit bytes as engine-parser text: printable ASCII verbatim, everything else as [0xNN]."""
    s = []
    for b in data:
        if 0x20 <= b < 0x7F and chr(b) not in "[]#/":
            s.append(chr(b))
        else:
            s.append("[0x%02X]" % b)
    return "".join(s)


def write_if_changed(path, content):
    if os.path.exists(path) and open(path, encoding="utf-8").read() == content:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)
    return True


def main():
    kernel = load_kernel_defs()
    alias = load_alias_defs([os.path.join(ROOT, "src", "Text", "codes.txt"),
                             os.path.join(GEN, "face_codes.txt")], kernel)
    msgs = read_messages(SRC_ROOT)
    names = set()
    lines = ["// generated by tools/gentext.py from src/Text — do not edit", ""]
    for name, body, path, ln, allow4 in msgs:
        if name in names:
            raise SyntaxError("%s:%d: duplicate message name %s" % (path, ln, name))
        names.add(name)
        data = encode_body(name, body, kernel, alias, "%s:%d" % (os.path.relpath(path, ROOT), ln))
        # FE8 shares the 4th face slot's sprite tiles (0x380-0x3FF) with moving-unit sprites: a 4th face
        # shown while any unit is mid-action gets overwritten. Only scenes marked allow-4-faces (checked
        # to run with no unit moving, e.g. a chapter opening after ENUN) may show four.
        if max_faces(data) > 3 and not allow4:
            raise SyntaxError("%s:%d: message %s shows %d faces at once; FE8 can only show 3 safely "
                              "(mark '// allow-4-faces' above it only if no unit can be moving)" % (
                                  os.path.relpath(path, ROOT), ln, name, max_faces(data)))
        lines += ["## " + name, to_clean_line(data), ""]
    write_if_changed(os.path.join(TEXTS, "bs_texts.txt"), "\n".join(lines))

    # combined defs: kernel defs + every raw byte, so the engine parser understands our clean output
    defs = open(os.path.join(TEXTS, "textdefs.txt"), encoding="utf-8").read().rstrip("\n") + "\n\n// raw bytes (tools/gentext.py)\n"
    defs += "".join("[0x%02X] = 0x%02X\n" % (b, b) for b in range(256))
    defs_path = os.path.join(GEN, "textdefs_all.txt")
    write_if_changed(defs_path, defs)

    root = os.path.join(TEXTS, "texts-bs.txt")
    write_if_changed(root, '#include "Source/vanilla_cropped.txt"\n#include "Source/kernel.txt"\n#include "bs_texts.txt"\n')

    control = tp.load_control_chars(defs_path)
    messages, _ = tp.process_file([], root, control, "utf8")
    for m in messages:
        tp.all_data.extend(m.data)
    freq = tp.GenerateFreqTable(tp.all_data)
    tree = tp.huffman.BuildHuffmanTree(freq)
    table = tp.huffman.BuildHuffmanTable()
    codes = tp.huffman.build_code_table(tree)

    import io
    buf = io.StringIO()
    tp.write_huffman_table(table, buf)
    buf.write("{\n")
    tp.write_all_compressed_data(messages, codes, buf)
    tp.write_text_table(messages, buf)
    buf.write("\n}\n")
    data = buf.getvalue()
    os.makedirs(os.path.join(TEXTS, "build"), exist_ok=True)
    write_if_changed(os.path.join(TEXTS, "build", "msg_data_cropped.event"), data)
    write_if_changed(os.path.join(TEXTS, "build", "msg_data.event"), data)

    ours = [m for m in messages if m.definiation in names]
    kern = [m for m in messages if m.definiation not in names]
    first = min(m.idx for m in ours) if ours else None
    assert all(m.idx >= first for m in ours) and all(m.idx < first for m in kern), "our messages must come last"
    hdr = io.StringIO()
    tp.write_header(kern, hdr)
    changed = write_if_changed(os.path.join(TEXTS, "build", "msgs.h"), hdr.getvalue())
    ev = ["// generated by tools/gentext.py — message IDs for Blade & Stone text"]
    ev += ["#define %s 0x%04X" % (m.definiation, m.idx) for m in ours]
    write_if_changed(os.path.join(GEN, "BsMsgs.event"), "\n".join(ev) + "\n")
    print("text: %d kernel/vanilla + %d Blade & Stone messages (ids 0x%04X-0x%04X)%s" % (
        len(kern), len(ours), first, first + len(ours) - 1, "; msgs.h changed" if changed else ""))
    if first + len(ours) > 0x2000:
        sys.exit("text table overflow: raise AllocMsgTable")


if __name__ == "__main__":
    try:
        main()
    except (SyntaxError, ValueError) as e:
        sys.exit("gentext: %s" % e)

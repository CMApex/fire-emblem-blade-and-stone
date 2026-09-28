"""play.py: run an input script against a ROM and produce a contact sheet of every `shot`.

usage: play.py ROM SCRIPT OUT.png [--load state] [--save state]
script lines: same as gbarun, plus `snap` (auto-numbered screenshot) and `rep N cmd...` (repeat).
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
GBARUN = os.path.join(HERE, "gbarun", "gbarun")


def run(rom, script_text, out, load=None, save=None, cols=4):
    tmp = tempfile.mkdtemp(prefix="play_", dir="/tmp/claude-0")
    lines, shots = [], []
    if load:
        lines.append("load " + load)
    for raw in script_text.splitlines():
        s = raw.split("#")[0].strip()
        if not s:
            continue
        reps = 1
        if s.startswith("rep "):
            _, n, s = s.split(" ", 2); reps = int(n)
        for _ in range(reps):
            if s.startswith("snap"):
                label = s[4:].strip()
                f = os.path.join(tmp, "s%03d.png" % len(shots))
                shots.append((f, label or str(len(shots))))
                lines.append("shot " + f)
            else:
                lines.append(s)
    if save:
        lines.append("save " + save)
    sp = os.path.join(tmp, "script.txt")
    open(sp, "w").write("\n".join(lines) + "\n")
    r = subprocess.run([GBARUN, rom, sp], capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode:
        print("gbarun failed:", r.stderr)
    if shots:
        cols = min(cols, len(shots))
        rows = (len(shots) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 244, rows * 176), (60, 0, 60))
        d = ImageDraw.Draw(sheet)
        for i, (f, label) in enumerate(shots):
            x, y = (i % cols) * 244 + 2, (i // cols) * 176 + 2
            if os.path.exists(f):
                sheet.paste(Image.open(f), (x, y))
            d.text((x + 2, y + 161), label, fill=(255, 255, 0))
        sheet.save(out)
    return [f for f, _ in shots]


if __name__ == "__main__":
    args = sys.argv[1:]
    load = save = None
    if "--load" in args:
        i = args.index("--load"); load = args[i + 1]; del args[i:i + 2]
    if "--save" in args:
        i = args.index("--save"); save = args[i + 1]; del args[i:i + 2]
    rom, script, out = args[:3]
    run(rom, open(script).read() if os.path.exists(script) else script.replace(";", "\n"), out, load, save)

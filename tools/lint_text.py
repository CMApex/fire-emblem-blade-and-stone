"""Flag dialogue lines likely too wide for the FE8 text box (split on box/line breaks)."""
import re, sys
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 35
for ln, line in enumerate(open(sys.argv[1]).read().split('\n'), 1):
    if line.startswith('//') or line.startswith('##'):
        continue
    parts = re.split(r'\[(?:A|NL|N|X|0x02|Open[A-Za-z]+|LoadFace\]\[[^\]]*\]\[[^\]]*|Load[A-Z][a-z]+)\]', line)
    for p in parts:
        vis = re.sub(r'\[[^\]]*\]', '', p)
        if len(vis) > LIMIT:
            print("%d: %d chars: %s" % (ln, len(vis), vis))

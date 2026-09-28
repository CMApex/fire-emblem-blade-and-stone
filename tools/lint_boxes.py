"""Find dialogue boxes with more than two lines (FE8 boxes hold two)."""
import re, sys
s = open(sys.argv[1]).read()
bad = 0
for block in re.split(r'\n## ', s):
    name = block.split('\n')[0]
    body = '\n'.join(block.split('\n')[1:])
    for seg in re.split(r'\[A\]|\[Open[A-Za-z]+\]', body):
        seg = re.sub(r'^(\s|\[NL\]|\[0x02\]|\[LoadOverworldFaces\]|\n)+', '', seg)
        if seg.count('[NL]') + seg.count('[N]') >= 2:
            bad += 1
            print(name, '| 3+ lines:', seg.replace('\n', '|')[:100])
sys.exit(1 if bad else 0)

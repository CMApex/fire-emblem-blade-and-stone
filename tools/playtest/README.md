# Playtest harness

Headless mGBA-based playtesting: a scripted emulator (`gbarun`) plus a bot that reads game RAM
(cursor, units, movement map, the Talk proc) and plays real turns — moving, attacking, visiting, talking,
seizing — taking screenshots throughout.

    sudo apt install libmgba-dev libpng-dev
    gcc -O2 -o gbarun gbarun.c -lmgba -lpng      # place at tools/playtest/gbarun/gbarun or adjust game.py
    python3 fullrun.py boot    # new game -> Prologue turn 1
    python3 fullrun.py p1      # play the Prologue to the seize
    python3 fullrun.py pend    # Prologue ending -> Chapter 1 turn 1
    python3 fullrun.py c1      # play Chapter 1 to the end

Paths inside the scripts assume the original workspace layout; edit ROM/state paths at the top of fullrun.py.

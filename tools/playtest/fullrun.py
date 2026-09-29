import sys, os; sys.path.insert(0,'/home/claude/work/tools')
from playchapter import *
ROM='/home/claude/work/blade-and-stone/build/BladeAndStone.gba'
S='/home/claude/work/states/'
OUT='/home/claude/work/shots/run/'
os.makedirs(OUT, exist_ok=True)
stage=sys.argv[1]
g=Game(ROM, None if stage=='boot' else S+'run_'+stage+'.ss'); g.wait(10)
P=Player(g)
def advance_until(cond, label, maxi=800, snap_every_dialog=1):
    n=0
    for i in range(maxi):
        if P.is_dialog():
            if n % snap_every_dialog == 0: g.shot('%s dlg%d'%(label,n))
            n+=1; g.press('A',50); continue
        if cond(): return True
        if i%10==0: g.shot('%s i%d'%(label,i))
        g.press('A',40)
    g.shot(label+' TIMEOUT'); return False
def deployed(cid): return any(u['cid']==cid and not (u['state']&0xD) and u['x']<0x40 for u in g.units('blue'))

if stage=='boot':
    for l in open('/home/claude/work/tools/newgame.txt'):
        if l.strip(): g.cmd(l.strip())
    n=0
    for i in range(1500):
        if P.is_dialog():
            if n%1==0: g.shot('intro dlg%d'%n)
            n+=1; g.press('A',50); continue
        if any(u['x']<0x40 for u in g.units('blue')):
            if g.turn()==(1,0) and P.is_idle(): break
            g.wait(40); continue            # never press A once units are on the map
        if i%10==0: g.shot('intro i%d'%i)
        g.press('A',40)
    g.save(S+'run_p1.ss'); g.sheet(OUT+'01_intro.png',cols=6)
elif stage=='p1':
    g.move_cursor(17,12); g.press('A',40); g.move_cursor(17,11); g.press('A',10); P.arrive(1,(17,11)); g.shot('visit menu'); g.press('A',45); P.settle('visit')
    r=play(g,P,[1,2,0x10,0x11],1,seize=(7,1),boss_pos=(7,1),lord_goal=(7,1),tag='P')
    print('prologue result',r,g.turn())
    g.save(S+'run_pend.ss'); g.sheet(OUT+'02_prologue.png',cols=6)
elif stage=='pend':
    n=0
    for i in range(1500):
        if P.is_dialog():
            g.shot('toch1 dlg%d'%n); n+=1; g.press('A',50); continue
        if any(u['cid']==0x24 and u['x']<0x40 for u in g.units('blue')):
            if g.turn()==(1,0) and P.is_idle(): break
            g.wait(40); continue            # never mash A once Chapter 1 units are on the map
        if i%10==0: g.shot('toch1 i%d'%i)
        g.press('A',40)
    print('cursor at ch1 start', g.cursor(), 'hector', [(u['x'],u['y']) for u in g.units('blue') if u['cid']==0x24])
    for k in range(3): g.wait(10); g.shot('ch1 start cursor f%d'%k)
    g.save(S+'run_c1.ss'); g.sheet(OUT+'03_to_ch1.png',cols=6)
elif stage=='c1':
    plans={0x27:{'visit':(8,2)}, 0x28:{'visit':(15,6)}, 0x23:{'talk':0x24}}
    r=play(g,P,[0x27,0x28,0x24,0x26,0x23],0x24,boss_pos=(6,20),lord_goal=(7,20),tag='C1',plans=plans,max_turns=25,
           done_check=lambda: P.is_dialog() and not any((r['x'],r['y'])==(6,20) for r in live(g,'red')))
    print('ch1 result',r,g.turn())
    g.save(S+'run_c1end.ss'); g.sheet(OUT+'04_ch1.png',cols=6)
elif stage=='c1end':
    # play out the ending; stop at the title screen, then open the file menu to check for a stale suspend
    for i in range(300):
        if P.is_dialog(): g.shot('end dlg%d'%i) if i%2==0 else None; g.press('A',50); continue
        if g.u32(0x0202BCF0+0x10)&0xFFFF==0 and i>5: break
        g.wait(40)
        if i%8==0: g.shot('end i%d'%i)
    g.wait(300); g.shot('title?')
    g.press('START',120); g.shot('file menu')
    g.sheet(OUT+'05_ch1_ending.png',cols=6)
g.close()

import sys; sys.path.insert(0,'/home/claude/work/tools')
from game import *; from autoplay import Player

def live(g, side):
    return [u for u in g.units(side) if not u['hidden'] and not u['dead'] and u['hp'] > 0]

def play(g, P, party, lord, seize=None, boss_pos=None, max_turns=20, tag='P', done_check=None, lord_goal=None, pre_turn=None, plans=None):
    plans = plans or {}
    """Play turns until done_check() is true or the chapter ends (turn counter reset / chapter changes)."""
    ch0 = g.u8(0x0202BCF0 + 0x0E)
    for _ in range(max_turns):
        t, ph = g.turn()
        if g.u8(0x0202BCF0 + 0x0E) != ch0:
            return 'chapter changed'
        if pre_turn: pre_turn(t)
        for cid in party:
            if g.turn()[0] != t: break
            us = [u for u in live(g, 'blue') if u['cid'] == cid and not (u['state'] & 2)]
            if not us: continue
            u = us[0]
            boss_alive = boss_pos is not None and any((r['x'], r['y']) == boss_pos for r in live(g, 'red'))
            sz = seize if (cid == lord and seize and not boss_alive) else None
            goal = (lord_goal if cid == lord else None)
            pl = plans.get(cid, {})
            res = P.do_unit(u, goal=pl.get('goal', goal), seize=sz, label='%s T%d c%X' % (tag, t, cid),
                            visit=pl.get('visit'), talk_to=pl.get('talk'))
            if res in ('visit', 'talk'):
                pl.pop('visit' if res == 'visit' else 'talk', None)
                if res == 'talk':   # talking doesn't end the turn (ContemporaryTalk): act again
                    u2 = [x for x in live(g, 'blue') if x['cid'] == cid and not (x['state'] & 2)]
                    if u2: P.do_unit(u2[0], goal=goal, label='%s T%d c%X post-talk' % (tag, t, cid))
            if res == 'seize':
                return 'seized'
            if g.u8(0x0202BCF0 + 0x0E) != ch0 or (boss_pos and not any((r['x'], r['y']) == boss_pos for r in live(g, 'red')) and seize is None):
                return 'boss down'
            if done_check and done_check():
                return 'done'
        if done_check and done_check():
            return 'done'
        if g.u8(0x0202BCF0 + 0x0E) != ch0:
            return 'chapter changed'
        if g.turn()[0] == t:
            if P.end_turn('%s T%d' % (tag, t)) is None:
                return 'stuck'
        else:
            P.settle('%s T%d auto' % (tag, t))
        print('%s turn %d done: blue %s | red %d' % (tag, t, [(u['cid'], u['x'], u['y'], u['hp']) for u in live(g, 'blue') if u['cid'] in party], len(live(g, 'red'))), flush=True)
    return 'max turns'

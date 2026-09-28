/* Blade & Stone — small core engine changes (C, built by the C-SkillSys makefile). */
#include "common-chax.h"

/**
 * Player leader per chapter.
 * Vanilla returns Eirika/Ephraim; with neither on the map the cursor, the
 * "leader died" checks and some menus have nobody to point at (the Ch. 1 bug).
 * gBsLeaderTable[chapter] names the leader; if that character isn't deployed
 * we fall back to the first living blue unit so the cursor always has a home.
 */
extern const u8 gBsLeaderTable[0x100];

LYN_REPLACE_CHECK(GetPlayerLeaderUnitId);
int GetPlayerLeaderUnitId(void)
{
	int i, pid = gBsLeaderTable[(u8)gPlaySt.chapterIndex];

	if (pid == 0)
		pid = CHARACTER_EIRIKA;

	if (GetUnitFromCharId(pid))
		return pid;

	for (i = FACTION_BLUE + 1; i < FACTION_BLUE + 0x40; i++) {
		struct Unit *unit = GetUnit(i);

		if (UNIT_IS_VALID(unit) && !(unit->state & US_UNAVAILABLE))
			return UNIT_CHAR_ID(unit);
	}
	return pid;
}

/**
 * ASMC: drop the suspend save. Used when the demo ends and we return to the title,
 * so no stale "Resume Chapter" is offered.
 */
void BS_ClearSuspendASMC(ProcPtr proc)
{
	InvalidateSuspendSave(SAVE_ID_SUSPEND);
}

/**
 * Vanilla bug fix: event cameras (CAM1 and friends) centre on a tile with
 * StoreAdjustedCameraPositions(), whose edge clamp tests "x + 8 > width - 1"
 * instead of the 15x10-tile screen. Centring near the right/bottom of a small
 * map therefore scrolled past the edge and showed garbage rows (seen in the
 * Prologue). Clamp to the real screen size.
 */
LYN_REPLACE_CHECK(StoreAdjustedCameraPositions);
void StoreAdjustedCameraPositions(int xIn, int yIn, int *xOut, int *yOut)
{
	int x = xIn - 7, y = yIn - 5;
	int xmax = gBmMapSize.x - 15, ymax = gBmMapSize.y - 10;

	if (x > xmax)
		x = xmax;
	if (y > ymax)
		y = ymax;
	if (x < 0)
		x = 0;
	if (y < 0)
		y = 0;

	*xOut = x;
	*yOut = y;
}

/**
 * QoL: skip the "Health and Safety" warning screen (jump straight to the logos,
 * exactly as a soft reset does).
 */
LYN_REPLACE_CHECK(PrepareHealthAndSafetyScreen);
void PrepareHealthAndSafetyScreen(struct ProcOpAnimHS *proc)
{
	Proc_Goto(proc, 0x3E7);
}

/**
 * QoL: new-game option defaults. Same as vanilla InitPlayConfig except
 * text speed = Fast and game (map movement) speed = Fast.
 */
LYN_REPLACE_CHECK(InitPlayConfig);
void InitPlayConfig(int isDifficult, s8 controller)
{
	CpuFill16(0, &gPlaySt, sizeof(gPlaySt));

	gPlaySt.chapterIndex = 0;

	if (isDifficult)
		gPlaySt.chapterStateBits |= PLAY_FLAG_HARD;

	gPlaySt.config.controller = controller;
	gPlaySt.config.animationType = 0;
	gPlaySt.config.disableTerrainDisplay = 0;
	gPlaySt.config.unitDisplayType = 0;
	gPlaySt.config.autoCursor = 0;
	gPlaySt.config.textSpeed = 2;       /* vanilla 1 (normal) */
	gPlaySt.config.gameSpeed = 1;       /* vanilla 0 (normal) */
	gPlaySt.config.disableBgm = 0;
	gPlaySt.config.disableSoundEffects = 0;
	gPlaySt.config.windowColor = 0;
	gPlaySt.config.disableAutoEndTurns = 0;
	gPlaySt.config.noSubtitleHelp = 0;
	gPlaySt.config.battleForecastType = 0;
	gPlaySt.config.debugControlRed = 0;
	gPlaySt.config.debugControlGreen = 0;
	gPlaySt.config.unitColor = 0;
	gPlaySt.config.unk41_5 = 0;
}

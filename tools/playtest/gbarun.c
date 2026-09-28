// gbarun: tiny headless mGBA harness for scripted playtesting.
// usage: gbarun rom.gba script.txt
// script commands (one per line, # comments):
//   wait N                 run N frames with no input
//   press KEY [N]          hold KEY(s) (comma-separated) for 4 frames, then release and wait N (default 10)
//   hold KEYS N            hold KEY(s) for N frames
//   shot path.png          screenshot current frame
//   save path / load path  save state / load state
//   peek8/peek16/peek32 ADDR   print value at bus address
//   poke8/poke16/poke32 ADDR VAL
//   echo text
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba/core/serialize.h>
#include <mgba/core/interface.h>
#include <mgba-util/vfs.h>
#include <png.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

static struct mCore* core;
static color_t* buffer;
static unsigned W, H;

static void quietLog(struct mLogger* l, int cat, enum mLogLevel lvl, const char* fmt, va_list args) {
	(void)l; (void)cat; (void)lvl; (void)fmt; (void)args;
}
static struct mLogger logger = { .log = quietLog };

static int keybit(const char* k) {
	static const char* names[] = {"A","B","SELECT","START","RIGHT","LEFT","UP","DOWN","R","L"};
	for (int i = 0; i < 10; ++i) if (!strcasecmp(k, names[i])) return 1 << i;
	fprintf(stderr, "bad key %s\n", k); exit(2);
}
static int keys(char* s) {
	int m = 0; char* save; for (char* t = strtok_r(s, ",+", &save); t; t = strtok_r(NULL, ",+", &save)) m |= keybit(t);
	return m;
}
static void frames(int n, int k) {
	core->setKeys(core, k);
	for (int i = 0; i < n; ++i) core->runFrame(core);
	core->setKeys(core, 0);
}
static void shot(const char* path) {
	FILE* f = fopen(path, "wb"); if (!f) { perror(path); return; }
	png_structp p = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
	png_infop info = png_create_info_struct(p);
	png_init_io(p, f);
	png_set_IHDR(p, info, W, H, 8, PNG_COLOR_TYPE_RGB, PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
	png_write_info(p, info);
	unsigned char* row = malloc(W * 3);
	for (unsigned y = 0; y < H; ++y) {
		for (unsigned x = 0; x < W; ++x) {
			uint32_t c = buffer[y * W + x];
			row[x*3+0] = c & 0xFF; row[x*3+1] = (c >> 8) & 0xFF; row[x*3+2] = (c >> 16) & 0xFF;
		}
		png_write_row(p, row);
	}
	png_write_end(p, NULL); png_destroy_write_struct(&p, &info); fclose(f); free(row);
}

int main(int argc, char** argv) {
	if (argc < 3) { fprintf(stderr, "usage: gbarun rom script\n"); return 1; }
	mLogSetDefaultLogger(&logger);
	core = mCoreFind(argv[1]);
	if (!core || !core->init(core)) { fprintf(stderr, "core init failed\n"); return 1; }
	core->desiredVideoDimensions(core, &W, &H);
	buffer = calloc(W * H, sizeof(color_t));
	core->setVideoBuffer(core, buffer, W);
	mCoreInitConfig(core, NULL);
	if (!mCoreLoadFile(core, argv[1])) { fprintf(stderr, "load failed\n"); return 1; }
	struct VFile* sav = VFileMemChunk(NULL, 0);
	core->loadSave(core, sav);
	core->reset(core);

	FILE* sf = strcmp(argv[2], "-") ? fopen(argv[2], "r") : stdin;
	if (!sf) { perror(argv[2]); return 1; }
	char line[512]; int ln = 0;
	while (fgets(line, sizeof line, sf)) {
		++ln;
		char* c = strchr(line, '#'); if (c) *c = 0;
		char cmd[64] = {0}, a[256] = {0}, b[256] = {0};
		int n = sscanf(line, "%63s %255s %255s", cmd, a, b);
		if (n < 1) continue;
		if (!strcmp(cmd, "wait")) frames(atoi(a), 0);
		else if (!strcmp(cmd, "press")) { frames(4, keys(a)); frames(n >= 3 ? atoi(b) : 10, 0); }
		else if (!strcmp(cmd, "hold")) frames(atoi(b), keys(a));
		else if (!strcmp(cmd, "shot")) shot(a);
		else if (!strcmp(cmd, "save")) { struct VFile* vf = VFileOpen(a, O_CREAT | O_TRUNC | O_RDWR); mCoreSaveStateNamed(core, vf, SAVESTATE_SAVEDATA | SAVESTATE_RTC); vf->close(vf); }
		else if (!strcmp(cmd, "load")) { struct VFile* vf = VFileOpen(a, O_RDONLY); if (!vf) { fprintf(stderr, "%d: no state %s\n", ln, a); return 1; } mCoreLoadStateNamed(core, vf, SAVESTATE_SAVEDATA | SAVESTATE_RTC); vf->close(vf); }
		else if (!strncmp(cmd, "peek", 4)) {
			uint32_t addr = strtoul(a, NULL, 0), v;
			if (cmd[4] == '8') v = core->busRead8(core, addr); else if (cmd[4] == '1') v = core->busRead16(core, addr); else v = core->busRead32(core, addr);
			printf("%s %08X = 0x%X (%u)\n", cmd, addr, v, v);
		}
		else if (!strncmp(cmd, "poke", 4)) {
			uint32_t addr = strtoul(a, NULL, 0), v = strtoul(b, NULL, 0);
			if (cmd[4] == '8') core->busWrite8(core, addr, v); else if (cmd[4] == '1') core->busWrite16(core, addr, v); else core->busWrite32(core, addr, v);
		}
		else if (!strcmp(cmd, "echo")) printf("%s", line + 5);
		else if (!strcmp(cmd, "ack")) printf("ACK\n");
		else if (!strcmp(cmd, "dump")) {
			uint32_t addr = strtoul(a, NULL, 0), len = strtoul(b, NULL, 0);
			printf("DUMP ");
			for (uint32_t i = 0; i < len; ++i) printf("%02X", core->busRead8(core, addr + i));
			printf("\n");
		}
		else { fprintf(stderr, "%d: unknown command %s\n", ln, cmd); return 1; }
		fflush(stdout);
	}
	core->deinit(core);
	return 0;
}

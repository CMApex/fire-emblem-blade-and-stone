#!/bin/bash
# Fetch and build everything the build needs, into this folder (nothing is installed system-wide):
#   engine/                    the pinned C-SkillSys engine and its submodules
#   engine/Tools/EventAssembler  ColorzCore (Linux build), lyn, compress, ea-dep, EA standard library
#   .toolchain/devkitpro/      grit + gbalzss (built from devkitPro's sources) and a devkitARM-style
#                              folder pointing at Ubuntu's arm-none-eabi gcc
# Needs the packages from ./install-deps.sh. Safe to re-run; it skips what is already built.
set -e
cd "$(dirname "$(readlink -f "$0")")"
ROOT="$PWD"

ENGINE_COMMIT=f61f6c20f5dfbd8bf2f436f01c40fbd2551d6ef8      # fe8u-cskillsys (LTS line)
EA_COMMIT=150e9eac999b39055c45239da1888afe00b8e2aa          # MokhaLeee/EventAssembler (mokha-fix)
CLIB_COMMIT=350399991a5bb8c1f8eb540edbb2f182f1f45db9        # MokhaLeee/FE-CLib-Mokha
PYTOOLS_COMMIT=bd11df297ccf5c7b82b5a737b685033978a26b7c     # StanHash/FE-PyTools
CHECKPATCH_COMMIT=3de754a2363efda6be9ded7c8d364a9bd224fcd3  # MokhaLeee/check_patch
COLORZ_COMMIT=67af0b27643a8ea8a01918742383065f5755d25b      # StanHash/ColorzCore
GRIT_COMMIT=5209ac206360dacf2a2e64d5a6a60ea3a38f512e        # devkitPro/grit
GBATOOLS_COMMIT=054d507f90d32784274b6cf7e03f1c43d02d7a57    # devkitPro/gba-tools (gbalzss)

# ---- preflight: say exactly what is missing instead of failing halfway
missing=()
for c in git make cmake gcc g++ re2c autoreconf libtoolize pkg-config python3 dotnet gawk sponge \
         arm-none-eabi-gcc arm-none-eabi-as arm-none-eabi-objcopy; do
  command -v "$c" >/dev/null || missing+=("$c")
done
python3 -c "import PIL, elftools" 2>/dev/null || missing+=("python3 modules Pillow/pyelftools")
pkg-config --exists freeimage 2>/dev/null || [ -f /usr/include/FreeImage.h ] || missing+=("libfreeimage-dev")
if [ ${#missing[@]} -gt 0 ]; then
  echo "setup: missing: ${missing[*]}"
  echo "setup: run ./install-deps.sh first (Ubuntu / WSL2)."
  exit 1
fi

pin() { # url dir commit [extra clone args]
  [ -d "$2/.git" ] || git clone -q "${@:4}" "$1" "$2"
  git -C "$2" cat-file -e "$3^{commit}" 2>/dev/null || git -C "$2" fetch -q origin "$3"
  git -C "$2" checkout -q "$3"
}
step() { echo "== $*"; }

step "engine sources"
pin https://github.com/FireEmblemUniverse/fe8u-cskillsys engine $ENGINE_COMMIT
pin https://github.com/MokhaLeee/EventAssembler.git engine/Tools/EventAssembler $EA_COMMIT
git -C engine/Tools/EventAssembler submodule update -q --init --recursive
pin https://github.com/MokhaLeee/FE-CLib-Mokha.git engine/Tools/FE-CLib-Mokha $CLIB_COMMIT
pin https://github.com/StanHash/FE-PyTools.git engine/Tools/FE-PyTools $PYTOOLS_COMMIT
git -C engine/Tools/FE-PyTools submodule update -q --init --recursive
pin https://github.com/MokhaLeee/check_patch.git engine/Tools/check_patch $CHECKPATCH_COMMIT

EA="$ROOT/engine/Tools/EventAssembler"
SRCS="$EA/.Sources"
if [ ! -x "$EA/Tools/lyn" ] || [ ! -x "$EA/ea-dep" ] || [ ! -x "$EA/Tools/compress" ] || [ ! -f "$EA/Tools/Tool Helpers.txt" ]; then
  step "Event Assembler tools (standard library, compress, lyn, ea-dep)"
  # This is engine/Tools/scripts/build_ea_wo_core.sh minus the Haskell formatting tools
  # (ParseFile/Png2Dmp/PortraitFormatter), which this build never calls.
  cp "$SRCS/EAStandardLibrary/EAstdlib.event" "$EA/"
  cp -R "$SRCS/EAStandardLibrary/Language Raws" "$SRCS/EAStandardLibrary/EA Standard Library" \
        "$SRCS/EAStandardLibrary/Extensions" "$EA/"
  mkdir -p "$EA/Tools"
  cp "$SRCS/Tool Helpers.txt" "$EA/Tools/"
  make -s -C "$SRCS/compress" && cp "$SRCS/compress/compress" "$EA/Tools/"
  for t in lyn ea-dep; do
    tmp=$(mktemp -d)
    src="$SRCS/$t"
    ( cd "$tmp" && cmake -S "$src" -B . -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build . -j"$(nproc)" >/dev/null )
    if [ "$t" = lyn ]; then cp "$tmp/lyn" "$EA/Tools/"; else cp "$tmp/ea-dep" "$EA/"; fi
    rm -rf "$tmp"
  done
fi

if [ ! -x "$EA/ColorzCore" ]; then
  step "ColorzCore (Linux build, needs the .NET 8 SDK)"
  pin https://github.com/StanHash/ColorzCore .toolchain/src/ColorzCore $COLORZ_COMMIT
  if ! DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 \
       dotnet publish .toolchain/src/ColorzCore/ColorzCore/ColorzCore.csproj -c Release -o "$EA" \
       > .toolchain/colorzcore-build.log 2>&1; then
    echo "setup: building ColorzCore failed; last lines of .toolchain/colorzcore-build.log:"
    grep -E "error" .toolchain/colorzcore-build.log | sort -u | tail -5
    echo "setup: (it downloads the .NET 6 reference pack from nuget.org, so it needs internet access)"
    exit 1
  fi
fi

DKP="$ROOT/.toolchain/devkitpro"
mkdir -p "$DKP/devkitARM/bin" "$DKP/tools/bin"
for t in gcc as ld ar nm objcopy objdump readelf strip; do
  ln -sf "$(command -v arm-none-eabi-$t)" "$DKP/devkitARM/bin/arm-none-eabi-$t"
done
build_autotools() { # repo dir commit binary
  [ -x "$DKP/tools/bin/$4" ] && return
  step "$4 (devkitPro)"
  pin "$1" ".toolchain/src/$2" "$3"
  local log="$ROOT/.toolchain/$4-build.log"
  # -include cstdint: gbalzss predates GCC 13, which no longer pulls <cstdint> in implicitly
  if ! ( cd ".toolchain/src/$2" && ./autogen.sh && ./configure --prefix="$DKP/tools" CXXFLAGS="-O2 -include cstdint" \
         && make -j"$(nproc)" "$4" && cp "$4" "$DKP/tools/bin/" ) > "$log" 2>&1; then
    echo "setup: building $4 failed; last lines of $log:"; tail -15 "$log"; exit 1
  fi
}
build_autotools https://github.com/devkitPro/grit.git grit $GRIT_COMMIT grit
build_autotools https://github.com/devkitPro/gba-tools.git gba-tools $GBATOOLS_COMMIT gbalzss

for f in "$EA/ColorzCore" "$EA/ea-dep" "$EA/EAstdlib.event" "$EA/Tools/lyn" "$EA/Tools/compress" "$DKP/tools/bin/grit" "$DKP/tools/bin/gbalzss"; do
  [ -e "$f" ] || { echo "setup: failed to build $f"; exit 1; }
done
echo "Setup done. Put your clean ROMs in roms/ (see README) and run ./build.sh"

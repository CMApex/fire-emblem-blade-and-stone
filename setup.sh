#!/bin/bash
# Fetch and build the pinned C-SkillSys engine into ./engine (not committed).
# Requirements (Linux/WSL): git, python3 (+Pillow, pyelftools), gcc-arm-none-eabi or devkitARM,
# cmake, make, ghc+cabal (EA formatting tools), .NET SDK 8 (ColorzCore), gawk, moreutils, and
# devkitPro's grit + gbalzss. See docs/build-notes.md for what each is used for.
set -e
cd "$(dirname "$(readlink -f "$0")")"

ENGINE_COMMIT=f61f6c20f5dfbd8bf2f436f01c40fbd2551d6ef8      # fe8u-cskillsys (LTS line)
EA_COMMIT=150e9eac999b39055c45239da1888afe00b8e2aa          # MokhaLeee/EventAssembler (mokha-fix)
CLIB_COMMIT=350399991a5bb8c1f8eb540edbb2f182f1f45db9        # MokhaLeee/FE-CLib-Mokha
PYTOOLS_COMMIT=bd11df297ccf5c7b82b5a737b685033978a26b7c     # StanHash/FE-PyTools
CHECKPATCH_COMMIT=3de754a2363efda6be9ded7c8d364a9bd224fcd3  # MokhaLeee/check_patch
COLORZ_COMMIT=67af0b27643a8ea8a01918742383065f5755d25b      # StanHash/ColorzCore

pin() { # url dir commit [extra clone args]
  [ -d "$2/.git" ] || git clone -q "${@:4}" "$1" "$2"
  git -C "$2" fetch -q origin "$3" 2>/dev/null || true
  git -C "$2" checkout -q "$3"
}

pin https://github.com/FireEmblemUniverse/fe8u-cskillsys engine $ENGINE_COMMIT
pin https://github.com/MokhaLeee/EventAssembler.git engine/Tools/EventAssembler $EA_COMMIT --recursive
git -C engine/Tools/EventAssembler submodule update -q --init --recursive
pin https://github.com/MokhaLeee/FE-CLib-Mokha.git engine/Tools/FE-CLib-Mokha $CLIB_COMMIT
pin https://github.com/StanHash/FE-PyTools.git engine/Tools/FE-PyTools $PYTOOLS_COMMIT --recursive
pin https://github.com/MokhaLeee/check_patch.git engine/Tools/check_patch $CHECKPATCH_COMMIT

# EA tools (lyn, compress, ea-dep, ParseFile, Png2Dmp, PortraitFormatter, stdlib)
cp engine/Tools/scripts/build_ea_wo_core.sh engine/Tools/EventAssembler/
( cd engine/Tools/EventAssembler && ./build_ea_wo_core.sh )

# ColorzCore (Linux build)
if [ ! -x engine/Tools/EventAssembler/ColorzCore ]; then
  pin https://github.com/StanHash/ColorzCore .colorzcore $COLORZ_COMMIT
  dotnet publish .colorzcore/ColorzCore/ColorzCore.csproj -c Release -o engine/Tools/EventAssembler
fi

echo "Engine ready. Put roms/fe8u.gba and roms/fe7u.gba in place, then run ./build.sh"

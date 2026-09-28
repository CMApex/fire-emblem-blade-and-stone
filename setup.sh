#!/bin/bash
# Fetch the FE8 Skill System base (pinned) underneath the Blade & Stone overlay.
# Existing Blade & Stone files are never overwritten.
set -e
cd "$(dirname "$(readlink -f "$0")")"
SS_COMMIT=65b959d7a16a4c24b8096f33bd79f0195138d423
if [ ! -d .ss_base ]; then
  git clone -q https://github.com/FireEmblemUniverse/SkillSystem_FE8 .ss_base
fi
( cd .ss_base && git checkout -q "$SS_COMMIT" )
( cd .ss_base && tar --exclude=.git -cf - . ) | tar -xkf - 2>/dev/null || true
chmod +x MakeHack.sh build.sh EventAssembler/ColorzCore EventAssembler/Tools/* 2>/dev/null || true
echo "Skill System base installed. Now: put roms/fe8u.gba and roms/fe7u.gba in place and run ./build.sh"

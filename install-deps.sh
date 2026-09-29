#!/bin/bash
# Install everything Blade & Stone needs to build, on Ubuntu 24.04 (the default WSL2 distro on Windows).
# Run once:  ./install-deps.sh      (asks for your password for apt)
# Then:      ./setup.sh && ./build.sh
set -e

if ! grep -qE 'VERSION_ID="2[4-9]\.' /etc/os-release 2>/dev/null; then
  echo "note: this was tested on Ubuntu 24.04; other versions may need different package names."
fi
SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO="sudo"

# gcc-arm-none-eabi lives in Ubuntu's "universe" component (enabled by default on WSL and desktop Ubuntu)
if ! grep -rqsE '^[^#]*\buniverse\b|^Components:.*\buniverse\b' /etc/apt/sources.list /etc/apt/sources.list.d/; then
  $SUDO apt-get update -q
  $SUDO apt-get install -y -q software-properties-common
  $SUDO add-apt-repository -y universe
fi

$SUDO apt-get update -q
$SUDO apt-get install -y -q --no-install-recommends \
  git ca-certificates make build-essential cmake re2c pkg-config \
  autoconf automake libtool libfreeimage-dev \
  gcc-arm-none-eabi binutils-arm-none-eabi libnewlib-arm-none-eabi \
  python3 python3-pil python3-pyelftools \
  dotnet-sdk-8.0 gawk moreutils

echo
echo "Dependencies installed. Next: ./setup.sh (fetches and builds the engine, ~5 minutes), then ./build.sh"
echo "Optional: install Tiled (https://www.mapeditor.org) to edit maps; on Windows use the Windows installer."

#!/usr/bin/env bash
set -e
shopt -s nullglob  # dont return the glob-pattern if nothing found
shopt -s globstar  # allow recursive globs
cd "$(realpath "$(dirname "$(realpath "$0")")/..")"

if [ ! -f requirements.txt ]; then
  echo "requirements.txt is missing"
  exit 1
fi

# create clean dist directory
mkdir -p "dist/"
[ -d "dist/jarklin/" ] && rm -rf "dist/jarklin/"

# copy source code
echo "Copying code..."
cp -Lr "src/jarklin/" "dist/jarklin/"
cp README.md "dist/jarklin/"

# cleanup of copied
find dist/jarklin -type d -iname __pycache__ -prune -exec rm -rf "{}" \;

# install dependencies into (new) copied source-code directory
echo "Installing dependencies..."
mkdir -p "dist/jarklin/_deps/"
python3 -m pip install -r "requirements.txt" -t "dist/jarklin/_deps/" --no-compile --disable-pip-version-check
dist_infos=$(find dist/jarklin/_deps/*.dist-info -maxdepth 0 -printf '%f\n')

echo "Installing scripts and other files..."
echo "Jarklin v$(./jarklin.sh --version | tr -d '\0') build
Python: $(python3 -V | awk '{print $2}')
pip:    $(pip3 --version | awk '{print $2}')
Dependencies Installed:
$(echo "$dist_infos" | sed 's/\.dist-info$//' | awk -F- '{print $1,$2}' | column -t | sed 's/^/ - /')
OS Detail:
$(sed 's/^/ /' /etc/os-release)
" > "dist/jarklin/meta.info"

cp build-files/jarklin.run dist/jarklin/jarklin
chmod +x dist/jarklin/jarklin

echo "Build successful"

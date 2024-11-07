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
cp requirements.txt "dist/jarklin/"

# cleanup of copied
find dist/jarklin -type d -iname __pycache__ -prune -exec rm -rf "{}" \;

echo "Installing scripts and other files..."

cp build-files/jarklin.run dist/jarklin/jarklin
chmod +x dist/jarklin/jarklin

mkdir -p dist/jarklin/web/web-ui/

echo "Build successful"

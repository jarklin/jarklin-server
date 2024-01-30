#!/usr/bin/env bash
set -e
set -e  # fail on any error
shopt -s nullglob  # dont return the glob-pattern if nothing found


function success() {
  echo -e "\e[32m" "$@" "\e[39m"
}

function error() {
  echo -e "\e[31m" "$@" "\e[39m"
}

function info() {
  echo -e "\e[33m" "$@" "\e[39m"
}


JARKLIN_ARCHIVE="jarklin.tgz"
WEB_UI_ARCHIVE="web-ui.tgz"
WEB_UI_DIR="jarklin/web/web-ui/"


# download new jarklin-source if not exists
if [ -f "$JARKLIN_ARCHIVE" ]; then
  info "$JARKLIN_ARCHIVE found. Using that"
else
  info "Downloading $JARKLIN_ARCHIVE..."
  wget "https://github.com/jarklin/jarklin/releases/download/latest/jarklin.tgz" -O "$JARKLIN_ARCHIVE"
fi

# archive thus keep old web-ui if user wants
if [ -n "$(ls -A "$WEB_UI_DIR" 2>/dev/null)" ]; then
  read -r -p "Old web-ui found. Do you want to keep that? [y/N] " response </dev/tty
  case "$response" in
    [yY][eE][sS]|[yY])
        tar -cvz -C "$WEB_UI_DIR" -f "$WEB_UI_ARCHIVE" .
        ;;
  esac
fi

# download new web-ui if not exists
if [ -f "$WEB_UI_ARCHIVE" ]; then
  info "$WEB_UI_ARCHIVE found. Using that"
else
    info "Downloading new web-ui..."
    wget "https://github.com/jarklin/jarklin-web/releases/download/latest/web-ui.tgz" -O "$WEB_UI_ARCHIVE"
fi

info "Extracting jarklin..."
tar -xf "$JARKLIN_ARCHIVE" -C "."
#rm "$JARKLIN_ARCHIVE"

info "Installing web-ui..."
tar -xf "$WEB_UI_ARCHIVE" -C "$WEB_UI_DIR"
#rm "$WEB_UI_ARCHIVE"

info "Installing dependencies..."
rm -rf "jarklin/_deps/"
mkdir -p "jarklin/_deps/"
python3 -m pip install -r "jarklin/requirements.txt" -t "jarklin/_deps/" --disable-pip-version-check

echo
success "Jarklin is now installed"
echo

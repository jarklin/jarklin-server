#!/usr/bin/env bash
set -e  # fail on any error
shopt -s nullglob  # dont return the glob-pattern if nothing found

if ! command -v whiptail >/dev/null; then
  echo -e "\e[31m whiptail not found. required for the wizard\e[39m"
  exit 1
fi
if ! command -v pip3 >/dev/null; then
  echo -e "\e[31m pip3 not found. required for some parts of the wizard\e[39m"
  exit 1
fi


ROOT="$(realpath "$(dirname "$(realpath "$0")")/")"


function success() {
  echo -e "\e[32m" "$@" "\e[39m"
}
function info() {
  echo -e "\e[33m" "$@" "\e[39m"
}
function error() {
  echo -e "\e[31m" "$@" "\e[39m"
}


# shellcheck disable=SC2120
function wiz_ask_directory() {
  SELECTED="."
  TITLE="Jarklin-Wizard"
  TEXT="Select a directory"

  while [[ $# -gt 0 ]]; do
    case $1 in
    --title)
        TITLE="$2"
        shift; shift;
      ;;
    --text)
        TEXT="$2"
        shift; shift;
      ;;
    *)
      if [ "$SELECTED" = "." ]; then
        SELECTED="$1"
      else
        echo "unknown parameter '$1'"
        exit 1
      fi
      ;;
    esac
  done

  SELECTED=$(realpath "$SELECTED")
  while true; do
    OPTIONS=("." "." ".." "..")
    for entry in "$SELECTED"/*/; do
      entry=$(basename "$entry")
      OPTIONS+=("$entry" "$entry")
    done
    CHOICE=$(
      whiptail --title "$TITLE" --menu "$TEXT\n$SELECTED" 20 60 10 --notags --nocancel --ok-button "Open" \
      "${OPTIONS[@]}" \
      3>&2 2>&1 1>&3
    )
    if [ "$CHOICE" = "." ]; then
      break
    fi
    SELECTED=$(realpath "$SELECTED/$CHOICE")
  done
  echo "$SELECTED"
}


function wiz_download_jarklin() {
    wget "https://github.com/jarklin/jarklin/releases/download/latest/jarklin.tgz" -O "$1"
}

function wiz_download_web_ui() {
    wget "https://github.com/jarklin/jarklin-web/releases/download/latest/web-ui.tgz" -O "$1"
}

function wizard_install() {
  FEATURES=$(
    whiptail --title "Jarklin-Wizard - Install" --checklist "Which features do you want to install?" 20 60 10 --notags --separate-output \
    "jarklin" "Jarklin server/backend" ON \
    "web-ui" "Default WEB-UI" ON \
    "better-exceptions" "Better exceptions logging" OFF \
    3>&2 2>&1 1>&3
#    "web.service" "jarklin-server.service" OFF \
#    "cache.service" "jarklin-cache.service" OFF \
  )
  JARKLIN=false
  WEB_UI=false
  BETTER_EXCEPTIONS=false
#  WEB_SERVICE=false
#  CACHE_SERVICE=false
  for FEATURE in $FEATURES; do
    case $FEATURE in
    "jarklin") JARKLIN=true ;;
    "web-ui") WEB_UI=true ;;
#    "web.service") WEB_SERVICE=true ;;
#    "cache.service") CACHE_SERVICE=true ;;
    "better-exception") BETTER_EXCEPTIONS=true;
    esac
  done

  if [ $JARKLIN = true ] && [ -d "./jarklin/" ] && ! whiptail --yesno "./jarklin/ seems to exist. It will be overwritten." 20 60 --yes-button "Continue" --no-button "Cancel"; then
    return 0;
  fi

  if [ $JARKLIN = true ]; then
    JARKLIN_ARCHIVE="./jarklin.tgz"
    info "Downloading Jarklin..."
    wiz_download_jarklin "$JARKLIN_ARCHIVE"
    info "Extracting Jarklin..."
    tar -xf "$JARKLIN_ARCHIVE" -C .
    rm "$JARKLIN_ARCHIVE"

    info "Installing dependencies..."
    rm -rf "jarklin/_deps/"
    mkdir -p "jarklin/_deps/"
    python3 -m pip install -r "jarklin/requirements.txt" -t "jarklin/_deps/" --disable-pip-version-check
  fi

  if [ $WEB_UI = true ]; then
    WEB_UI_ARCHIVE="./web-ui.tgz"
    WEB_UI_DIR="./jarklin/web/web-ui/"
    info "Downloading Web-UI..."
    wiz_download_web_ui "$WEB_UI_ARCHIVE"
    mkdir -p "$WEB_UI_DIR"
    info "Extracting Web-UI..."
    tar -xf "$WEB_UI_ARCHIVE" -C "$WEB_UI_DIR"
    rm "$WEB_UI_ARCHIVE"
  fi

  if [ $BETTER_EXCEPTIONS = true ]; then
    info "Installing better-exceptions..."
    python3 -m pip install -U better-exceptions -t "jarklin/_deps/" --disable-pip-version-check
  fi

  whiptail --title "Jarklin-Wizard - Install" --msgbox "Jarklin was successfully installed" 20 60
}

function wizard_update() {
  cd "$ROOT"
  whiptail --title "Jarklin-Wizard - Update" --msgbox "Update is currently not available.\nReinstalling should do the job." 20 60
}

function wizard_uninstall() {
#  whiptail --title "Jarklin-Wizard - Uninstall" --msgbox "Uninstall" 20 60
  cd "$ROOT/../"  # folder above jarklin
  # cant find jarklin-executable which means was started via `wget wizard.sh | bash` or so
  if [ ! -f "./jarklin/jarklin" ] || [ "$("./jarklin/jarklin" --verify-jarklin)" != "jarklin" ]; then
    whiptail --title "Jarklin-Wizard - Uninstall" --msgbox "Could not find Jarklin installation\n($(pwd))" 20 60
    return 0
  fi
  if whiptail --title "$TITLE - Auth" --yesno "Are you sure want to uninstall Jarklin?\n$ROOT" 20 60; then
    rm -rf "./jarklin"
    whiptail --title "Jarklin-Wizard - Uninstall" --msgbox "Jarklin was uninstalled" 20 60
  fi
}

function wizard_create_config() {
  TITLE="Jarklin-Wizard - Create Config"

  DEST=$(wiz_ask_directory --title "$TITLE" --text "Select where you want to create the config-file")
  FP="$DEST/.jarklin.yaml"

  BASEURL=$(
    whiptail --title "$TITLE - Server" --inputbox "Under which baseurl do you want to serve jarklin?" 20 60 "/" 3>&2 2>&1 1>&3
  )

  if whiptail --title "$TITLE - Server" --yesno "Bind to a Port or Unix-Domain-Socket (UDS)?" --yes-button "Port" --no-button "UDS" 20 60; then
    HOST=$(
      whiptail --title "$TITLE - Server" --inputbox "Host:" 20 60 "localhost" 3>&2 2>&1 1>&3
    )
    PORT=$(
      whiptail --title "$TITLE - Server" --inputbox "Port:" 20 60 "9898" 3>&2 2>&1 1>&3
    )
  else
    UDS=$(
      whiptail --title "$TITLE - Server" --inputbox "Where should the UDS be placed" 20 60 "/tmp/jarklin.sock" 3>&2 2>&1 1>&3
    )
  fi

  if whiptail --title "$TITLE - Server" --yesno "Whether to gzip the content. Reduces the response-size and thus loading time of text-based responses on cost of CPU-Time.
note: Should be done by the Proxy-Server if possible. Otherwise, this is the option." 20 60; then
    GZIP="yes"
  else
    GZIP="no"
  fi

  if whiptail --title "$TITLE - Server" --yesno "Allow media optimization.
Enabling this option allows for faster downloads as supported media is just-in-time optimized.
Important: only use this option for a very small userbase as it can take up lots of system-resources." 20 60; then
    OPTIMIZE=true
  else
    OPTIMIZE=false
  fi

  if whiptail --title "$TITLE - Auth" --yesno "Do you want to require authentication?" 20 60; then
    USERNAME=$(
      whiptail --title "$TITLE - Auth" --inputbox "Username:" 20 60 3>&2 2>&1 1>&3
    )
    PASSWORD=$(
      whiptail --title "$TITLE - Auth" --passwordbox "Password:" 20 60 3>&2 2>&1 1>&3
    )
  fi

  if whiptail --title "$TITLE - Filtering" --yesno "Should the content be whitelisted or blacklisted?
Whitelist: directories or files are allowed/enabled
Blacklist: directories or files are disabled/hidden" --yes-button "Whitelist" --no-button "Blacklist" 20 60; then
    WHITELIST=true
  else
    WHITELIST=false
  fi

  LOGGINGLEVEL=$(whiptail --title "$TITLE" --menu "How detailed should the logs be?" 20 60 10 --notags \
    "CRITICAL" "CRITICAL" \
    "ERROR" "ERROR" \
    "WARNING" "WARNING" \
    "INFO" "INFO" \
    "DEBUG" "DEBUG" \
    3>&2 2>&1 1>&3
  )

  if whiptail --title "$TITLE - Logging" --yesno "Should the logs be saved to a file?" 20 60; then
    LOG2FILE=true
  else
    LOG2FILE=false
  fi

  {
    echo "web:"
    if [ -n "$BASEURL" ]; then
      echo "  baseurl: \"$BASEURL\""
    fi
    echo "  server:"
    if [ -n "$UDS" ]; then
      echo "    unix_socket: \"$UDS\""
    else
      echo "    host: \"$HOST\""
      echo "    port: $PORT"
    fi
    echo "#    threads: 4"
    echo "  gzip: $GZIP"
    if [ $OPTIMIZE = true ]; then
      echo "  optimize: yes"
    fi
    if [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
      echo "  auth:"
      echo "    username: \"$USERNAME\""
      echo "    password: \"$PASSWORD\""
    fi
    echo "cache:"
    echo "  ignore:"
    if [ $WHITELIST = true ]; then
      echo "    - \"/*\""
      echo "#    - \"!/allowed\""
    else
      echo "#    - \"/hidden\""
    fi
    echo "logging:"
    echo "  level: $LOGGINGLEVEL"
    if [ $LOG2FILE = true ]; then
      echo "  file:"
    fi

  } > "$FP"

  whiptail --title "$TITLE" --msgbox "Config file was created
$FP

For more or detailed options see https://jarklin.github.io/config/config-options" 20 60
}

function wizard_main() {
  CWD="$(pwd)"
  while true; do
    cd "$CWD"  # reset in case a sub-command changes the directory
    CHOICE=$(whiptail --title "Jarklin-Wizard" --menu "What do you want to do?" 20 60 10 --nocancel --notags \
      "wizard_install" "Install Jarklin" \
      "wizard_uninstall" "Uninstall Jarklin" \
      "wizard_create_config" "Generate a new config" \
      "exit" "Exit the Wizard" \
      3>&2 2>&1 1>&3
#      "wizard_update" "Update Jarklin" \
      )
    "$CHOICE"
  done
}

case $1 in
install)
  wizard_install ;;
uninstall)
  wizard_uninstall ;;
"")  # no command
  wizard_main "${@:2}" ;;
-h | --help)
  echo "wizard [-h|--help]"
#  echo "wizard install  -  install jarklin"
#  echo "wizard uninstall  -  uninstall jarklin"
;;
*)
  error "Unknown command '$1'"
  exit 1
;;
esac

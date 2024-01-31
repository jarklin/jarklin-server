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

# shellcheck disable=SC2120
function wiz_ask_directory {
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
      echo "unknown parameter '$1'"
      exit 1
      ;;
    esac
  done

  SELECTED=$(realpath ".")
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
    wget -q "https://github.com/jarklin/jarklin/releases/download/latest/jarklin.tgz" -O "$1"
}

function wiz_download_web_ui() {
    wget -q "https://github.com/jarklin/jarklin-web/releases/download/latest/web-ui.tgz" -O "$1"
}

function wizard_install() {
  whiptail --title "Jarklin-Wizard - Install" --msgbox "Install" 20 60
}

function wizard_update() {
  CWD=$(pwd)
  cd "$ROOT"
  whiptail --title "Jarklin-Wizard - Update" --msgbox "Update" 20 60
  cd "$CWD"
}

function wizard_uninstall() {
  whiptail --title "Jarklin-Wizard - Uninstall" --msgbox "Uninstall" 20 60
}

function wizard_create_config() {
  TITLE="Jarklin-Wizard - Create Config"

  DEST=$(wiz_ask_directory --title "$TITLE" --text "Select where you want to create the config-file")
  FP="$DEST/.jarklin.yaml"

  if whiptail --title "$TITLE - Server" --yesno "Bind to Port or Unix-Domain-Socket (UDS)?" --yes-button "Port" --no-button "UDS" 20 60; then
    HOST=$(
      whiptail --title "$TITLE - Server" --inputbox "Host:" 20 60 "localhost" 3>&2 2>&1 1>&3
    )
    PORT=$(
      whiptail --title "$TITLE - Server" --inputbox "Port:" 20 60 "9898" 3>&2 2>&1 1>&3
    )
  else
    UDS=$(
      whiptail --title "$TITLE - Server" --inputbox "Where should the UDS be placed" 20 60 3>&2 2>&1 1>&3
    )
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
    echo "  server:"
    if [ -n "$UDS" ]; then
      echo "    unix_socket: \"$UDS\""
    else
      echo "    host: \"$HOST\""
      echo "    port: $PORT"
    fi
    echo "#    threads: 4"
    if [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
      echo "  auth:"
      echo "    username: \"$USERNAME\""
      echo "    password: \"$PASSWORD\""
    fi
    echo "ignore:"
    if [ $WHITELIST = true ]; then
      echo "  - \"/*\""
      echo "#  - \"!/allowed\""
    else
      echo "#  - \"/hidden\""
    fi
    echo "logging:"
    echo "  level: $LOGGINGLEVEL"
    if [ $LOG2FILE = true ]; then
      echo "  file:"
    fi

  } > "$FP"

  whiptail --title "$TITLE" --msgbox "Config file was created\n$FP" 20 60
}

function wizard_main() {
  while true; do
    CHOICE=$(whiptail --title "Jarklin-Wizard" --menu "What do you want to do?" 20 60 10 --nocancel --notags \
      "install" "Install Jarklin" \
      "update" "Update Jarklin" \
      "uninstall" "Uninstall Jarklin" \
      "create_config" "Generate a new config" \
      "exit" "Exit the Wizard" \
      3>&2 2>&1 1>&3
      )
    case $CHOICE in
    "install")
      wizard_install ;;
    "update")
      wizard_install ;;
    "uninstall")
      wizard_uninstall ;;
    "create_config")
      wizard_create_config ;;
    "exit")
      exit 0 ;;
    esac
  done
}

wizard_main

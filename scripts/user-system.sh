#!/usr/bin/env bash
set -e  # fail on any error
shopt -s nullglob  # dont return the glob-pattern if nothing found

#if ! command -v whiptail >/dev/null; then
#  echo -e "\e[31m whiptail not found. required for the wizard\e[39m"
#  exit 1
#fi

#ROOT="$(dirname "$(realpath "${BASH_SOURCE[0]:-$0}")")"
CWD="$(realpath "$(pwd)")"
PWFILE="$CWD/.jarklin/users"


function success() {
  echo -e "\e[32m" "$@" "\e[39m"
}
function info() {
  echo -e "\e[33m" "$@" "\e[39m"
}
function error() {
  echo -e "\e[31m" "$@" "\e[39m"
}


function verify() {
  if [ ! -f "$PWFILE" ]; then
    error "Missing users file"
    info "Either you are in the wrong location or you have to call '${BASH_SOURCE[0]} init'"
    return 1
  fi
}


function user_exist() {
  username="$1"
  if [ -z "$username" ]; then
    error "missing parameter: 'username'"
    exit 1
  fi
  while read -r line; do
    uname="${line%%:*}"
    if [ "$uname" = "$username" ]; then
      return 0
    fi
  done < "$PWFILE"
  return 1
}


function init() {
  mkdir -p "$(dirname "$PWFILE")"
  touch "$PWFILE"
}


function list_users() {
  while read -r line; do
    username="${line%%:*}"
    echo "$username"
  done < "$PWFILE"
}


function add_user() {
  username="$1"
  password="$2"
  if [ -z "$username" ]; then
    error "missing parameter: 'username'"
    return 1
  fi
  if [ -z "$password" ]; then
    error "missing parameter: 'password'"
    return 1
  fi
  if user_exist "$username"; then
    error "User already exist"
    return 1
  fi
  salt=$(openssl rand -base64 32)
  pwhash=$(openssl passwd -6 -salt "$salt" "$password")
  echo "$username:$pwhash" >> "$PWFILE"
}

function remove_user() {
  username="$1"
  if [ -z "$username" ]; then
    error "missing parameter: 'username'"
    return 1
  fi
  if ! user_exist "$username"; then
    error "User does not exist"
    return 1
  fi

  tmpfile="$(mktemp)"
  trap 'rm -f -- "$tmpfile"' EXIT

  while read -r line; do
    uname="${line%%:*}"
    if [[ "$uname" != "$username" ]]; then
      echo "$line" >> "$tmpfile"
    fi
  done < "$PWFILE"
  cat "$tmpfile" > "$PWFILE"
}

case $1 in
init)
  init "${@:2}" ;;
exist)
  verify
  user_exist "${@:2}" ;;
add)
  verify
  add_user "${@:2}" ;;
remove)
  verify
  remove_user "${@:2}" ;;
list)
  verify
  list_users "${@:2}" ;;
#"")  # no command
#  verify
#  interactive_main "${@:2}" ;;
-h | --help)
#  echo "user-system   - interactive Shell-UI"
  echo "user-system [-h|--help]"
  echo "user-system init"
  echo "user-system list"
  echo "user-system add <username> <password>"
  echo "user-system remove <username>"
;;
*)
  error "Unknown command '$1'"
  exit 1
;;
esac

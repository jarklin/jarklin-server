#!/usr/bin/env bash
################################################################################
# Template for small shell scripts with a CLI                                  #
# ---------------------------------------------------------------------------- #
# This file was taken from the utilities-sh project:                           #
# https://github.com/utility-libraries/utilities-sh/tree/main/shell-cli-template
################################################################################
# utility commands
################################################################################
set -e  # fail on any error
shopt -s nullglob  # dont return the glob-pattern if nothing found

ROOT="$(realpath "$(dirname "$(realpath "$0")")/")"
cd "$ROOT"

################################################################################
# utility
################################################################################

# usage: echo -e f"{FGG}Colored Text${FG}"
FGG="\e[32m"  # foreground-green
FGR="\e[31m"  # foreground-red
FGY="\e[33m"  # foreground-yellow
FG="\e[39m"  # foreground restore (to default)

function success() {
  echo -e -n "${FGG}"
  echo -n "$@"
  echo -e "${FG}"
}

function error() {
  echo -e -n "${FGR}Error:${FG} "
  echo "$@"
}

function warn() {
  echo -e -n "${FGY}Warning:${FG} "
  echo "$@"
}

################################################################################
# commands
################################################################################

# {your commands here}

################################################################################
# execution
################################################################################

function print_help() {
    echo "util.sh {help}"
}

case "$1" in
"help" | "--help" | "-h" | "")
  print_help "${@:2}"
;;
*)
  warn "Unknown command '$1'"
  print_help
  exit 1
;;
esac

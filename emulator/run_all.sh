#!/bin/sh
# Runs every experiment in the brief's order. One command per experiment also works: .venv/bin/python eN.py
# (baselines.py and e2.py first: E10 needs the E2 weights.)
cd "$(dirname "$0")"; PY=.venv/bin/python
run() { echo "$(date +%T) start $1"; FLOOD_WORKERS=${FLOOD_WORKERS:-2} $PY -u $1.py > $1.log 2>&1; echo "$(date +%T) end $1 (exit $?)"; }
for e in "$@"; do
  case $e in *+*) for p in $(echo $e | tr + ' '); do run $p & done; wait;; *) run $e;; esac
done

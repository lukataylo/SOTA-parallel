#!/bin/zsh
# Overnight chain for the complete solver map. Usage: fill/map_overnight.sh <air|pro> <own sign> <other sign> [colours to run first ...]
# Own sign forward, then confirm own movers, then help with the other sign from the far end. Restarts a step if it dies. Pushes results every 15 minutes.
M=$1; OWN=$2; OTHER=$3; shift 3; cd "$(dirname "$0")/.."
( while true; do sleep 900; git add results/$M/map >/dev/null 2>&1; git commit -q -m "$M: solver map runs

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>" >/dev/null 2>&1; git pull -q --rebase >/dev/null 2>&1; git push -q >/dev/null 2>&1; done ) &
SYNC=$!
step() { n=0; until caffeinate -i uv run -q --with mlx --with numpy python "$@"; do n=$((n+1)); [ $n -ge 5 ] && break; sleep 30; done }
step fill/map_run.py $OWN $M forward "$@"
step fill/map_confirm.py $OWN $M
git pull -q --rebase >/dev/null 2>&1
step fill/map_run.py $OTHER $M reverse
kill $SYNC; git add results/$M/map; git commit -q -m "$M: solver map finished"; git pull -q --rebase; git push -q; echo "overnight chain finished"

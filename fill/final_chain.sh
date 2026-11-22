#!/bin/zsh
# fill/final_chain.sh <air|pro> <job> [job ...]   then the same jobs from the far end are NOT run: use a second call with 'reverse' by hand if helping.
M=$1; shift; cd "$(dirname "$0")/.."
( while true; do sleep 600; git add results/$M/final >/dev/null 2>&1; git commit -q -m "$M: Sunday checks, runs

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>" >/dev/null 2>&1; git pull -q --rebase >/dev/null 2>&1; git push -q >/dev/null 2>&1; done ) &
SYNC=$!
for J in "$@"; do n=0; until caffeinate -i uv run -q --with mlx --with numpy python fill/final_runs.py ${=J} $M; do n=$((n+1)); [ $n -ge 4 ] && break; sleep 20; done; done
kill $SYNC; git add results/$M/final; git commit -q -m "$M: Sunday checks finished

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"; git pull -q --rebase; git push -q; echo "chain finished"

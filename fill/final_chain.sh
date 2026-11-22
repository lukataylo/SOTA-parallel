#!/bin/zsh
# fill/final_chain.sh <air|pro> <job> [job ...]   A job written as name:reverse is run from the far end.
M=$1; shift; cd "$(dirname "$0")/.."
( while true; do sleep 600; git add results/$M/final >/dev/null 2>&1; git commit -q -m "$M: Sunday checks, runs

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>" >/dev/null 2>&1; git pull -q --rebase >/dev/null 2>&1; git push -q >/dev/null 2>&1; done ) &
SYNC=$!
for J in "$@"; do
  A=("${(@s.:.)J}"); n=0
  until caffeinate -i uv run -q --with mlx --with numpy python fill/final_runs.py $A[1] $M $A[2]; do n=$((n+1)); [ $n -ge 4 ] && break; sleep 20; done
  [ "$A[1]" = "slice70" ] && uv run -q --with numpy python fill/slice70_plan.py && caffeinate -i uv run -q --with mlx --with numpy python fill/final_runs.py slice70s $M
done
kill $SYNC; git add results/$M/final; git commit -q -m "$M: Sunday checks finished

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"; git pull -q --rebase; git push -q; echo "chain finished"

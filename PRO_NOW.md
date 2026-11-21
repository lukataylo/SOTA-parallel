# PRO AGENT: current order (Air clock Sat 21:05). This file always holds your one current job.

**Stop the depth-change audit now. Start the overnight map.** The map tests every square of the tile in the solver, so it answers the audit's question over all ground, not a sample. Every GPU-minute on the audit is a minute the map loses.

## Do this, in order

1. Stop any solver job you have running. Commit and push what the audit has produced so far; do not score or extend it.
2. `git pull`
3. Start the chain and leave it running all night, on mains power:

   ```
   nohup fill/map_overnight.sh pro lower raise 13 29 281 304 425 633 > results/pro/map_overnight.log 2>&1 &
   ```

4. After about 3 minutes, check the first batch:

   ```
   uv run --with numpy python -c "import sys; sys.path.insert(0,'fill'); import map_lib as L; print(L.attribute('lower')[1])"
   ```

   Expect `max_imbalance` under 5e-5, `base_spread` 0.0, `unattributed` 0, and `moved` above 0.
5. Write one line at the top of `status/pro.md`: "Map started at HH:MM, pre-flight: <the printed numbers>". Push it. That line is how the Air knows you started.

## What the chain does by itself

- Lowered map: 900 solver runs, about 5 hours. One file per run in `results/pro/map/s1_lower/`.
- Then `fill/map_confirm.py lower pro`: re-runs its movers, up to 100 runs.
- Then helps the Air's raised map from the far end.
- Resumes if it dies. Commits and pushes `results/pro/map/` every 15 minutes.

## Rules for tonight

- Nothing else on the GPU until the chain prints "overnight chain finished".
- Do not change spacing, block size, depth, threshold or run order. They are fixed in `docs/G_CRITERIA.md` (last section), committed before any run.
- Do not start an experiment of your own. If you think something else is worth running, write it at the top of `status/pro.md` and keep the chain running; the Air or the human will answer.
- If the chain fails five times in a row, write the error at the top of `status/pro.md` and push.

## Why this and not something else

Plan: `docs/mythos/11_overnight_plan.md`. The Air is running the raised half now (17 s per run, 37 of 900 done at 21:04). The Air's pre-flight found 7 of 7 known movers within 0.06 mm of their single runs.

A note on clocks: the Air's earlier status entries tonight were labelled up to an hour ahead of the real time. Go by commit order, not by the times in headings.

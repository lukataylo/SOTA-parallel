# Packed what-ifs (bet G): pass lines fixed before any run

From `docs/mythos/10_parallelism_bets.md`. Committed before the solver has run any packed terrain.

## The idea

One storm already saturates the GPU, so batching more storms buys nothing. The way to get more what-ifs per second is more what-ifs per simulation: put several ground changes that cannot interact into one terrain, run it once, and read each change's effect from the receptors near it. This is the same trick as colouring a sparse Jacobian.

## How patches are packed

- Reach of a single patch, measured in the 360 single runs we hold: no receptor further than 57 m from a patch moved by 1 cm. (At 3 mm: 93 m. At 1 mm: 165 m.)
- Two patches may share a terrain only if their centres are at least **120 m** apart and the fill model does not predict that they move the same receptor.
- Greedy colouring; each colour is one terrain. A patch's verdict is read from the receptors within **60 m** of it (excluding those within 7.5 m, as in the control experiment).

## Experiment

1. **Repack the control experiment.** The same 120 patches, packed, at the same three storms. Compare with the 360 single runs in `results/air/p1_chunks/`.
2. **Planted movers.** 20 terrains, each holding one patch already confirmed to move a receptor by 1 cm plus as many freshly drawn dismissed patches as the 120 m rule allows, at the storm where that mover acts.

## Pass lines

- At least **30 of the 33** flagged patches keep their single-run verdict (moves a receptor by 1 cm, or does not) in every storm.
- **No** new 1 cm mover among the 87 dismissed and random patches.
- Median difference between packed and single change in peak depth is at most **1 mm**, over receptor-patch pairs that moved by 1 mm or more in the single runs.
- At least **19 of 20** planted movers are recovered.

## If it fails

Reported as: small ground changes interact in the solver at a separation of X m. That is a negative result, and it bears on the do-no-harm finding.

## What it is for

If it passes, the audit of the screen becomes affordable: about 3,000 randomly drawn dismissed what-ifs in a few dozen runs, which is what a recall statement needs. The current 0 of 87 cannot support one.

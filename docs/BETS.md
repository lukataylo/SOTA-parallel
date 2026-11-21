# Three frontier bets, Saturday evening

The human asked to work on all three. Source: `docs/mythos/4_frontier_bets.md` (Mythos's proposals, in full) and `docs/mythos/3_premortem_review.md` (its review of what we had). Pass lines below are fixed before each experiment runs. A random-ground control goes in every experiment. Failures are reported.

Running underneath all three: the control experiment in `docs/P1_CRITERIA.md` (363 solver runs, started on the Air at about 15:50, about 2.6 hours).

## Bet 1: measure where it matters

**Claim to test.** Knowing the height of under 1% of the ground collapses the uncertainty in each building's critical rainfall; knowing the same area of random ground does not.

| Step | Where | Pass line |
|---|---|---|
| Fill model, 100 terrains, three arms, fixed reference level | Air CPU | Decisive ground cuts median spread by at least 40%; random ground by at most 10% |
| Solver pilot: 8 terrains x 6 rain levels x 2 arms (96 runs, about 33 min) | Pro GPU | The "known" arm's spread is at most 75% of the unknown arm's |
| Full: 3 arms x 30 terrains x 12 rain levels (1,080 runs, about 6 h) | Pro GPU overnight | Reported as measured |
| Field: scan the three highest-leverage reachable spots, twice each | Human, Sunday 08:30 | Predictions committed before the walk |

**State.** First selection method (pass-cell patch tests, `fill/bet1_cpu.py`): 24% cut, random 0%. Below the 40% line. Second method (ground chosen from a 600-terrain ensemble, tested on 100 held-out terrains, `fill/bet1_cpu2.py`): running.

## Bet 2: one sweep instead of 2,132 rebuilds

**Claim to test.** The depression tree can be differentiated exactly, so one reverse sweep gives every building's threshold sensitivity to every cell, replacing a terrain rebuild per patch.

**Pass line (by 21:00).** Against the 2,132 brute-force patch tests in `results/air/decisive.npz`: recovers at least 90% of the 188 active patches; at most 5% false positives; matches size within 20% on at least 80%; at least 50x faster on one core.

**State.** Being built on the Air (`fill/sweep.py`).

## Bet 3: do-no-harm design

**Claim to test.** A small set of 5 cm patches can raise many buildings' critical rainfall while lowering none, and the solver confirms it; a naive choice harms neighbours.

| Step | Where | Pass line |
|---|---|---|
| Search with fill effects deflated by 0.6 | Air CPU | Best design of at most 5 patches lifts at least 5 buildings by 10%, and is harm-free |
| One design in the solver | GPU, 2 min | At least 60% of predicted beneficiaries drop by 1 cm or more; no receptor rises by 1 cm |
| 20 designs x 3 storms, including deliberately bad ones | GPU, 25 min | Reported as measured |

**Dependency.** This bet uses the fill model's sizes, so it needs the 0.6 understood. The control experiment gives the slope per storm level.

## For the Pro agent, when back

1. `uv run --with mlx --with numpy python fill/p1_run.py reverse` to take half the control experiment (it writes the same chunk files as the Air's forward run; commit `results/air/p1_chunks/` when done).
2. Then the Bet 1 solver pilot, if `status/air.md` says the fill-model step passed. Case files will be in `shared/`.
3. Dropped from the earlier list: the friction test, more work on the moving-water correction, non-triangular storms.

## Bet 5: response curves, not derivatives (added Saturday 18:15, from `docs/mythos/7_premortem_iphone_more_bets.md`)

**Claim to test.** The response of a building's critical rainfall to the height of a patch of ground is not a slope. It is a curve with a dead band (changes that do nothing), a one-sided slope, and a saturation. Three numbers per (patch, building) pair describe it, and from them we can map how wrong each square metre can be before any building moves.

**Experiment.** For every (patch location, building) pair that was active in the 2,132 patch tests, compute the exact critical rainfall for the patch height changed from -20 cm to +20 cm in 1 cm steps, with the exact fast re-evaluation (`fill/sweep.py`). Fit, separately for raising and lowering, a dead band, a slope and a saturation level.

**Pass line.** The three-number form fits within 0.5 mm of critical rain (the grid step) at every one of the 41 heights for at least 80% of pairs. Kill below 60%.

**Free check, reported regardless.** Do the curves, read at +/-5 cm, do better than the fill model's local slope on the 21 remote solver patches already run?

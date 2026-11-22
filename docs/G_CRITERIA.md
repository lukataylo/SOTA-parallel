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

---

# Pool test of the dismissed ground (added Saturday 20:05, lines fixed before any run)

## The idea

The fast model dismisses 97% of the ground, and the simulator has agreed on a sample (0 of 87). A sample cannot support a statement about how much the screen misses. Patches that do nothing can share one terrain far more densely than patches that do something. So: put many dismissed patches into one terrain, run it once, and if no building moves, all of them are cleared together. If a building moves, split the pool until the patch responsible is isolated or the pool is cleared.

## Design

- **What is tested.** The tile is cut into non-overlapping 5 x 5 m blocks. A block is tested if its centre cell is open ground and the whole-tile map (`results/air/atlas.npz`) says a 5 cm change there moves no building, for the sign being tested. Each such block is tested raised and lowered.
- **Pools.** Blocks are assigned by position to 64 classes, so blocks in one pool are 40 m apart. Within a pool the signs alternate in a checkerboard, so the pool adds and removes equal ground and does not shift the overall water volume. Each pool is run twice, once with every sign flipped, so each block is tested both ways. 128 terrains.
- **Storm.** One: the centred 40-minute storm with 35 mm of net rain (the middle storm of the control experiment).
- **Positive controls.** 10 further pools, each with one patch already confirmed to move a building by 1 cm added to it. These must trip.
- **A pool trips** if any building's peak depth differs from the unchanged run by 1 cm or more.

## Lines

- **Sensitivity:** at least 9 of the 10 positive-control pools trip. If not, pooling hides movers and the test is void.
- **Workable:** at most 25% of the 128 pools trip. If more, pooling at 40 m does not work, and it is rerun at 80 m.
- **Every tripped pool is split** in halves and rerun until each half is cleared or a single patch is isolated.
- **Reported, whatever it is:** the number of dismissed patches that move a building by 1 cm on their own, out of the number tested. That count, with the confirmed flagged patches, gives the screen's recall for this storm.

## What would count as failure

A single-patch miss rate above 1% of tested blocks. Then the fast model is not a safe screen, and the headline changes.


## The complete solver map (committed Saturday 21:50, before any run)

Plan: `docs/mythos/11_overnight_plan.md`. Runner: `fill/map_run.py`. Shared code for attribution: `fill/map_lib.py`.

**Design.** Every 5 x 5 m block of the tile with open ground (7,894 blocks; the outermost ring excluded), raised 5 cm and lowered 5 cm, at the 35 mm storm. Blocks are packed by colour (block row mod 30, block column mod 30): 900 terrains per sign, patches 150 m apart, 8.8 what-ifs per run. Colours run in a fixed random order (seed 2026), so any prefix is a uniform sample of the tile; the six colours holding the largest known single movers of each sign run first as a pre-flight and are excluded from any "uniform sample" statement. Air raises; Pro lowers; whichever finishes first helps the other from the far end.

**Why 150 m and not 120 m.** Mythos set a gate: use 120 m only if no receptor in the 276 single runs moved 1 cm more than 60 m from every patch. Three of 62 moved receptors did (68 to 76 m, 1.0 to 1.1 cm). So the spacing is 150 m and the 15 mm storm is dropped, as the gate prescribes.

**Attribution.** A receptor moves if its peak differs from the unchanged run by 1 cm or more. It is assigned to the nearest block in that run. If that block is more than 75 m away the move is "unattributed". A block is a remote mover if it moves a receptor more than 7.5 m from its centre.

**Confirm stage** (`fill/map_confirm.py`). Each machine re-runs its own sign's movers, at most 100 runs: 40 true singles of randomly drawn movers, then movers repacked 300 m apart, largest first.

**Pass lines.**

| Line | Pass |
|---|---|
| Integrity | Mass imbalance at most 5e-5 in every run; the unchanged run at the start and end identical at receptors |
| Packing holds at scale | Of the 276 earlier singles, at least 95% keep their verdict in the map; at least 36 of 40 true singles and at least 90% of repacked movers keep theirs; median difference in the change at most 1 mm; unattributed moves at most 2% of moved receptors |
| Screen (both rules scored as they stand, neither adjusted) | Misses at most 1% of the what-ifs it dismisses; flags at least 80% of remote movers. Rule 1: the whole-tile map (changes some building's critical rain depth). Rule 2: fill-predicted depth change of 1 mm or more at a receptor more than 7.5 m away at this storm (`fill/map_fill.py`, computed before scoring) |

**Not to be done after launch:** changing spacing, block size, depth, threshold or either screen rule. No more pool tests. Say "8.8 what-ifs per run" as measured, not a rounder number, and "we did not find" rather than "first".

### Result (scored Sunday 01:10; `fill/map_score.py`, `fill/map_trace_score.py`)

All 1,800 runs finished: 15,788 what-ifs, 8.77 per run. With the 126 confirm runs and 30 trace runs it is 1,956 runs, 8.07 per run.

| Line | Result | Verdict |
|---|---|---|
| Integrity | Worst mass imbalance 1.2e-5. Start and end unchanged runs identical on each machine. Air and Pro differ by 0.03 mm, so each run is compared with its own machine's unchanged run | Pass |
| 276 earlier singles keep their verdict | 274 of 276 (99.3%); median difference 0.02 mm | Pass |
| True singles keep their verdict | 68 of 73 (93%; line 90%) | Pass |
| Repacked movers keep theirs | 96 of 103 (93%; line 90%) | Pass |
| Median difference in the change | 0.00 mm | Pass |
| Unattributed moves at most 2% | 18 of 379 (4.75%) | **Fail** |
| Screen rule 1: misses at most 1% of dismissed | 61 of 15,270 (0.40%) | Pass |
| Screen rule 1: flags at least 80% of movers | 42 of 103 (41%) | **Fail** |
| Screen rule 2: misses at most 1% of dismissed | 29 of 15,182 (0.19%) | Pass |
| Screen rule 2: flags at least 80% of movers | 74 of 103 (72%) | **Fail** |

**Why the unattributed line failed, traced after scoring (`fill/map_trace.py`, 30 single runs, no line changed).** The 18 unattributed moves and the 7 movers that did nothing when re-run alone are the same thing: a block that changes the level of a long pond moves buildings 76 to 124 m away, further than the 75 m reach the attribution rule assumed. Each of the 25 was reproduced by one block of the same colour run on its own, to within 2 mm. So the packed runs add up correctly; what failed is "nearest block within 75 m" as a way to name the block. The confirm stage caught every wrong name.

**Final list:** 96 confirmed movers plus 2 found only by tracing: 98 of 15,788 what-ifs (0.62%), on 84 of 7,894 blocks (1.06%). 60 make a building deeper, 38 shallower. Median distance to the building 20 m, 90th percentile 49 m; 86% are more than 10 m away. Median effect 1.7 cm, largest 7.8 cm. 39 buildings affected. Against this list rule 2 finds 75 of 98 (77%) and rule 1 finds 42 (43%).

**What the slides may say.** "Every open 5 x 5 m square raised and lowered 5 cm in a 2D solver: 15,788 what-ifs in 1,800 runs. 98 move a building by 1 cm, typically 20 m away." And, since the screen failed its recall line: "The quick estimate finds 77% of the ground that matters and wrongly dismisses 0.15%. The solver map is the product; the quick estimate is a prior." Not to be said: that 150 m spacing isolates every change. It does not for long ponds; the confirm stage is part of the method.

## Sunday morning checks (committed 05:20, before any of these runs)

From `docs/mythos/12_premortem_two_hours.md`. Runner `fill/final_runs.py`, scorer `fill/final_score.py`. No number of the map above changes; these are new experiments with their own lines.

| Check | Runs | Pass line | If it fails we say |
|---|---|---|---|
| **Persist.** The 98 mover what-ifs, each alone, at the 70 mm storm; at 35 mm with Manning n 0.03 in place of 0.015; and at 15 mm | 3 x 99 | At 70 mm and at n 0.03: at least 66 of 98 move the same receptor by 1 cm in the same direction. 15 mm is reported with no line | "Which ground matters depends on the storm; the map is needed per storm" |
| **Dense.** The lowered half re-mapped with squares 75 m apart (block mod 15): 225 runs, 35 what-ifs per run | 226 | At least 95% of the 34 known lowered movers show their receptor move 1 cm the same way in the run that holds them. After tracing, zero moves that are not explained by a known mover (either this run's, within 125 m) | "At 75 m packing loses X%. The reach of water sets the factor; 150 m is near the limit here" |
| **Random dismissed.** 240 what-ifs drawn with seed 2026 from those the map did not call movers, each alone | 241 | 0 of 240 move a receptor more than 7.5 m away by 1 cm | "The map misses about X%" |
| **Design from the map.** Up to five mover what-ifs whose single run lowers a building 1 cm and raises no receptor more than 0.3 cm, distinct target buildings, largest benefit first; combined into one terrain | 1 | Every target falls 1 cm; no receptor rises 1 cm; every receptor's change within 5 mm of the sum of the single effects | "Single effects do not add up; every design needs its own run" |

"Persist" tests whether known movers remain movers. It does not look for new movers at other storms.

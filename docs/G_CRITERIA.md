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

## Sunday morning checks (committed 05:04, before any of these runs)

From `docs/mythos/12_premortem_two_hours.md`. Runner `fill/final_runs.py`, scorer `fill/final_score.py`. No number of the map above changes; these are new experiments with their own lines.

| Check | Runs | Pass line | If it fails we say |
|---|---|---|---|
| **Persist.** The 98 mover what-ifs, each alone, at the 70 mm storm; at 35 mm with Manning n 0.03 in place of 0.015; and at 15 mm | 3 x 99 | At 70 mm and at n 0.03: at least 66 of 98 move the same receptor by 1 cm in the same direction. 15 mm is reported with no line | "Which ground matters depends on the storm; the map is needed per storm" |
| **Dense.** The lowered half re-mapped with squares 75 m apart (block mod 15): 225 runs, 35 what-ifs per run | 226 | At least 95% of the 34 known lowered movers show their receptor move 1 cm the same way in the run that holds them. After tracing, zero moves that are not explained by a known mover (either this run's, within 125 m) | "At 75 m packing loses X%. The reach of water sets the factor; 150 m is near the limit here" |
| **Random dismissed.** 240 what-ifs drawn with seed 2026 from those the map did not call movers, each alone | 241 | 0 of 240 move a receptor more than 7.5 m away by 1 cm | "The map misses about X%" |
| **Design from the map.** Up to five mover what-ifs whose single run lowers a building 1 cm and raises no receptor more than 0.3 cm, distinct target buildings, largest benefit first; combined into one terrain | 1 | Every target falls 1 cm; no receptor rises 1 cm; every receptor's change within 5 mm of the sum of the single effects | "Single effects do not add up; every design needs its own run" |

"Persist" tests whether known movers remain movers. It does not look for new movers at other storms.

## Cloud GPU scaling: WITHDRAWN, not run (Sunday 05:35)

Withdrawn on the human's instruction to use no more compute than is provided. One 20-second port check ran on a rented A100 before that instruction; no number from it is used anywhere. The scaling run was stopped before it produced a result. The text below is kept only as a record of what was committed.

The solver is ported from MLX to PyTorch (`cloud/flood_torch.py`, same scheme, float32) and run on rented NVIDIA GPUs through Modal (`cloud/modal_map.py`).

| Check | Pass line | If it fails |
|---|---|---|
| **The port is the same solver.** The unchanged run and the first 240 raised colours of the map (seed-2026 order), 2,100 or so what-ifs | Peak depth at all 207 receptors within 0.1 mm of the laptop result in every run; mass imbalance at most 5e-5 | No cloud number is used |
| **Scaling.** The same 240 packed runs split over 1, 2, 4 and 8 GPUs (more if the account allows), 30 runs per batch | With 8 GPUs, solve time at least 5.6x shorter than with 1 (70% efficiency), measured on warm containers. Wall-clock including container start is reported beside it | We report the curve as measured and say where it bends |

The hardware gain (one cloud GPU against one laptop) is reported as a separate number and never multiplied into the 8.8 as one claim without saying which part is which.

## Changes to the Sunday checks (committed 05:40, before any of the affected runs; from `docs/mythos/13_parallel_speedup_on_brief.md`)

- **Baseline for the speedup, stated once.** One simulation per changed square per storm, the practice of the published CityCAT study (arXiv 2311.00420). Held fixed: the same MLX solver, laptops, 35 mm storm, grid, 15,788 what-ifs and 1 cm verdict. Our cost is 1,956 runs including confirm and trace runs. The baseline cost is the measured mean seconds per run times 15,788, extrapolated and said to be so. The 8x is per storm and is never multiplied by a number of storms.
- **Random dismissed is cut to 120**: every second what-if of the committed seed-2026 draw of 240 (even positions). Line unchanged: 0 move a receptor. The claim becomes "the map misses under 2.5%". If the Pro runs, it does the full 240.
- **New: packed map at the 70 mm storm, a slice.** One unchanged run, then the first 80 colours in seed-2026 order, raised and lowered (160 packed runs, about 1,400 what-ifs), attributed as in the 35 mm map. Then each mover alone, at most 40, largest effect first. **Line:** at least 90% of those movers keep their verdict alone. The number of movers not on the 35 mm list is reported with no line. If it fails we say: "Water reaches further in a bigger storm; the spacing, and so the speedup, must be set per storm."
- Order on the Air: persist at 70 mm and at n 0.03 (running), dense, the 70 mm slice, random dismissed, persist at 15 mm last if time allows. Stop by the clock at 11:00, never by results.

## Three further experiments (committed Sunday 06:10, before any of these runs)

Asked for by the human after a review of what the work does not yet show. Order on the Air: dense (running), derivative, random dismissed, drainage, the 70 mm slice. Persist at 15 mm is dropped.

**1. Would a derivative have found the same ground?** An adjoint (reverse-mode) flood model gives the slope of a building's peak water with respect to every ground cell. We have no adjoint code and storing 18,000 steps for one is beyond a laptop. What we can measure is the same quantity by a small change: each what-if re-run alone with 5 mm in place of 5 cm, and the result multiplied by ten. This is a small-perturbation slope, the thing an adjoint computes; it is not an adjoint run and is never called one.
- Runs: the 98 movers and the 120 random dismissed what-ifs, each alone at 5 mm, same sign (218 runs).
- Line: the slope is an adequate substitute if it names at least 90% of the 98 movers (ten times the 5 mm change is 1 cm or more, same receptor, same direction) and flags at most 1% of the dismissed that the solver did not move.
- If adequate we say: "A derivative would have found this map; an adjoint solver is the cheaper route and we did not build one." If not: "Ten times a 5 mm change found X% of the ground a 5 cm change moves and falsely flagged Y%: kerb-sized changes are not small."

**2. Drainage at inlets in place of a uniform loss.** We have no sewer or gully data. The constant 12 mm/h loss is replaced by synthetic road gullies: in every 25 m square that contains road, the lowest road cell becomes an inlet. Every inlet takes water standing on it at the same rate, set so that all inlets together can take exactly what the uniform loss could (12 mm/h over all open ground). Rain is applied in full. This changes where water is removed, not how much could be. It is not real drainage.
- Runs: the unchanged terrain and the 98 movers alone, 35 mm storm (99 runs).
- Line: at least 66 of 98 move the same receptor 1 cm the same way, as for the other persistence checks.
- If it fails we say: "Which ground matters depends on how drainage is represented. Real inlet and sewer data are needed before any street-level use."

**3. Recorded floods.** No door-level record exists for this tile. The London Fire Brigade publishes every incident with a location rounded to about 50 m. If flooding call-outs on the two storm days of July 2021 (12th and 25th) fall inside the tile, we compare them with simulated peak depth. The line is committed separately once the number of incidents is known and before any comparison. With fewer than 10 incidents the result is reported as anecdote, with no line.

### Recorded floods: result (Sunday 06:20). Too few to test anything; no line set, no comparison made

London Fire Brigade incident records (London Datastore, 2009 to October 2026; locations given as the centre of a 100 m cell; exact locations withheld for dwellings).

- Flooding call-outs inside the tile on 12 July 2021: 0. On 25 July 2021: 1 by its rounded location, a restaurant whose exact location is 14 m outside the tile's east edge. Within 500 m of the tile on those two days: 2.
- London-wide the same records show 582 flooding call-outs on 12 July 2021, so the storm is in the data; it did not produce calls here.
- Over all years the tile has 88 "Flooding" call-outs, 70 of them at dwellings and never more than 2 on one day. The category has no cause field and is mostly plumbing.
- Under the rule committed above (fewer than 10 incidents: anecdote, no line), nothing is compared with the model. The honest statement stays: this tile has no recorded rain flood to validate against. A validation needs a different tile, chosen where the July 2021 call-outs cluster; the same records would support that.

## Sunday results as they land (07:47)

- **Dense re-map at 75 m (lowered half): PASS.** 225 runs, 7,894 what-ifs, 35.1 per run. Known lowered movers seen: 34 of 34 (line 95%). One move had no known mover within 125 m: receptor 206, lower block (48,56), 9 m away. Traced with one single run (`fill/dense_trace.py`): alone it moves that receptor 0.996 cm, just under the 1 cm line; packed at 75 m it read 1.00 cm. So it is the block's own effect, pushed over the line by about 0.04 mm, not a new mover. After tracing, zero unexplained. Only the lowered half was tested at 75 m and no confirm runs were made at that spacing, so the reported speedup stays 8.1x.
- **Derivative (ten times a 5 mm change): mover half FAILS the line.** It names 54 of 98 movers (55%; line 90%). Predicted over true effect: median 0.71, quartiles 0.24 to 1.26. False flags among the dismissed are scored when the random-dismissed runs finish (0 of 23 so far).
- **Persist at Manning n 0.03: PASS**, 81 of 98. **Persist at 70 mm: FAIL**, 53 of 98.
- **Random dismissed, alone: PASS (08:10).** 0 of 120 move a building 1 cm (line 0); largest change 0.80 cm. The map misses under 2.5%.
- **Derivative, false flags: PASS.** 0 of 120 dismissed what-ifs falsely flagged. The derivative check as a whole fails on the mover half (55%, line 90%).

## Dense re-map, raised half (committed Sunday 08:15, before the run)

The lowered half passed at 75 m. The raised half is run the same way after the current queue: 225 runs, squares 75 m apart, each raised 5 cm (`fill/final_runs.py denseup`).
- **Line:** at least 95% of the 64 known raised movers show their receptor move 1 cm the same way in the run that holds them. After tracing with single runs, zero moves that are not explained by a known mover within 125 m.
- **If both halves pass we say:** "Packed at 75 m, 450 runs see every finding of the 1,800-run map and nothing new." The all-in run count for a 75 m map is 450 plus one confirm run per candidate it raises (counted from the data by `fill/final_score.py`), and the factor from that count is reported beside the 8.1x, which stays the figure for the map we fully confirmed. The 75 m candidates were not themselves run alone; that is said.
- **If it fails we say:** "Raising ground reaches further than lowering it; 75 m works for one half only."
- Stop by the clock at 11:00. If it is not finished, the count done is reported with no verdict.

## Order change (Sunday 09:38, no line changed)

The laptop slept for about 35 minutes during the 70 mm slice, so the queue would have passed 11:00. The 70 mm slice was stopped at 59 of 161 runs and the raised half at 75 m is run first; the 70 mm slice resumes after it. Whatever is unfinished at 11:00 is reported as a count with no verdict.

- **Drainage at inlets: PASS (09:36).** 79 of 98 move the same building 1 cm the same way (line 66). Receptors at 0.10 m or more: 30 with the uniform loss, 30 with inlets. The inlets are synthetic, not real drainage.

## At the 11:00 stop (Sunday)

All runs were stopped by a timer at 11:00.
- **Dense re-map, raised half: no verdict (incomplete).** 167 of 225 runs, 5,972 what-ifs, 35.8 per run. Known raised movers seen: 38 of 38 in the runs done (the other 26 known raised movers are in runs that did not happen). Moves with no known mover within 125 m: 0. Candidates a 75 m map would send to a confirm run: 48 in these 167 runs; 37 in the 225 lowered runs.
- **What we say:** "Packed at 75 m, every known finding the runs covered was seen again (72 of 72) and nothing new appeared; the raised half was three quarters done at the stop." The 75 m candidates were not run alone. The reported speedup stays 8.1x.
- **Packed map at 70 mm: no verdict.** 59 of 161 runs; not scored.
- **Drainage at inlets: PASS**, 79 of 98. **Random dismissed: PASS**, 0 of 120. **Derivative: FAIL**, 54 of 98 named (line 90%); 0 of 120 falsely flagged.

## Shortcut model as a filter: one after-the-fact test (committed Sunday 13:58, before scoring the split)

The two committed rules failed as scored (rule 1: 42 of 98; rule 2: 75 of 98) and that result stands. We now know whole-tile totals for some variants (sign-free rule 2: 80 of 98; rule 1 or rule 2: 83 of 98), so anything below is a consistency check on the same tile, not a clean test. From `docs/mythos/16_improving_the_shortcut.md`.

- **Candidates, fixed now:** A, rule 2 ignoring the sign of the change (a square is flagged for both raise and lower if either is flagged); B, rule 1 or rule 2; C, rule 1 or A.
- **Split:** by the centre of the square: west half is column below 256, east half is 256 and above.
- **Choice:** on the west half only, take the candidate with the fewest flags that flags at least 80% of the west movers. If none does, stop and report the fail.
- **Score once on the east half.** Pass: at least 80% of east movers flagged, at most 10% of east what-ifs flagged, at most 1% of dismissed east what-ifs are movers. Fewer than 30 movers in the east half counts as inconclusive. Recall without the railway wall point (receptor 161) is reported beside it.
- **Whatever happens we say:** the pre-committed rules failed; a rule chosen afterwards is a hypothesis for the next tile.
- Not done for lack of time: re-running the fill model at 70 mm and scoring on the unfinished 70 mm map.

**Result of the split test (Sunday 14:00): FAIL.** On the west half, candidate A (rule 2 ignoring sign) was the smallest that reached 80%: 32 of 36 movers with 3.5% of what-ifs flagged. Scored once on the east half it finds 48 of 62 (77%; line 80%), flags 7.4% and wrongly dismisses 0.19%. Without the railway wall point it finds 40 of 47 (85%). Rule 2 as committed finds 44 of 62 (71%) on the same half. So a rule chosen afterwards does not pass either. What we say: "The shortcut concentrates about three quarters of the ground that matters into a few percent of the squares, so it ranks ground, but it cannot safely dismiss it. It models where water rests, not how high it gets on the way." `fill/screen_split.py`.

## Shortcut model re-run at other rain depths (committed Sunday 14:04, before the run)

Asked for by the human: re-run the shortcut with the parameters most likely to pass. The parameter with a physical reason behind it is the amount of water. The shortcut computes resting water for 35 mm; the solver's peak has more water in transit, so a fill at a larger depth may resemble the peak better. This is a third look at the same tile: the east half has already been scored once (candidate A, 48 of 62). It cannot turn the committed fail into a pass; it can only give a hypothesis for the next tile.

- **Run:** `fill/map_fill_depths.py`: every square, both signs, the shortcut evaluated at 25, 35, 43, 50, 60 and 70 mm of water. A depth "fires" if the predicted change is 1 mm or more at a wall point more than 7.5 m away.
- **Candidates, fixed now, all ignoring the sign of the change:** D1, fires at 43 mm (the rain before the drains' share); D2, fires at any of 35, 43, 50; D3, fires at any of the six depths.
- **Choice on the west half only** (column below 256): the candidate with the fewest flags that flags at least 80% of west movers. **Scored once on the east half.** Pass: at least 80% of east movers, at most 10% of east what-ifs flagged, at most 1% wrongly dismissed. Recall without the railway wall point reported beside it.
- If the run is not finished by 14:45 it is stopped and reported as unfinished.

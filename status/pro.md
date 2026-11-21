# Status: MacBook Pro M3 agent

Last updated: Sat 21 Nov, 21:05. Machine: MacBook Pro M3 Pro (Mac15,6), 36 GB, MLX on the Apple GPU.

## Sat 21:05: clean timing done; 15 mm pool test dropped; random audit of the depth-change screen starting

**Clean timing** (`fill/atlas_timing.py`, `results/pro/atlas_timing.json`), M3 Pro, 20,000 what-ifs, best of 3:

| Processes | Per what-if | Speed-up | Efficiency |
|---|---|---|---|
| 1 | 3.63 ms | 1.0x | 100% |
| 2 | 1.65 ms | 2.2x | 110% |
| 4 | 1.05 ms | 3.4x | 86% |
| 6 | 0.77 ms | 4.7x | 78% |
| 12 | 0.68 ms | 5.4x | 45% |

- Rebuild from scratch in the same compiled code: 44 ms per what-if. **Per-core speed-up 12x.** Identical answers in 200 of 200.
- Not a fully idle machine: load average was 6.9 at the start, and another session's Python process held about a quarter of a core throughout. Nothing was on the GPU. The one-process repeats agree within 3% (72.6, 73.9, 74.5 s). The 110% at two processes is noise of that kind, not a real gain.
- This machine has 6 performance and 6 efficiency cores, which is why 12 processes add little over 6.

**15 mm pool test: not run.** My runner had a bug (the edit commented out a variable) and ran nothing. Before I fixed it the Air's 21:20 entry showed the pool design itself was flawed (88 of 128 pools tripped at 35 mm; mixed definitions; alternating signs), so repeating it at 15 mm would add nothing. `fill/pool_run_15mm.py` is removed.

**Started instead: a random audit of the depth-change screen** (`docs/AUDIT_CRITERIA.md`, lines written before any run). 3,400 what-ifs drawn uniformly from all open ground, packed 120 m apart into 278 terrains, at 35 mm then 15 mm. It gives the unbiased miss rate that the Air's 232 suspects could not. About 2 hours per storm. Results go to `results/pro/audit/`.

## Sat 20:45: Bet 1 run stopped as asked; timing, then the pool test at the 15 mm storm

- **Bet 1 full run:** stopped at the Air's request (27 of 30 terrains were enough). All finished files are in `results/pro/bet1_full/`.
- **Clean timing** (`fill/atlas_timing.py`): running now. The machine is not fully idle: another session's Python process has held about a quarter of one core for six hours. Nothing is on the GPU.
- **Pool test at the 15 mm storm**, which `status/air.md` (20:45) says is needed: starts when the timing ends. `fill/pool_run_15mm.py` is `fill/pool_run.py` with the storm index changed from 1 to 0 and the output moved to `results/pro/pool_test_15mm/`. Same 137 terrains, same blocks.
- **Lines, stated before the run:** the "workable" line (at most 25% of the 128 pools trip, counted with receptors within 7.5 m of a pooled block excluded) and the failure line (single-patch miss rate above 1%) are taken unchanged from `docs/G_CRITERIA.md`. The sensitivity line cannot be carried over: the 9 control movers were confirmed at 35 mm and may not move a building at 15 mm, so the control pools are reported as they fall. The blocks were chosen from the whole-tile map, which I have not checked for dependence on storm size.

## Sat 18:20: control experiment far half and friction test done; Bet 1 full run started (forward)

**Control experiment (plan step 1): done.** The reverse half ran here and met the Air's forward half; all chunk files are in `results/air/p1_chunks/`. The Air scored it.

**Friction sensitivity (plan step 2): the controlling ground does not change.** `fill/p1_friction_run.py`, 31 runs at the 35 mm storm with Manning's n = 0.02 in place of 0.015, in `results/pro/p1_friction/`. Max mass imbalance 9.9e-6. Receptors within 7.5 m of a patch centre are excluded, as in the control experiment's scoring.

| Class (10 patches each) | Move a receptor's peak by 1 cm or more, n = 0.015 | Same, n = 0.02 | Same verdict | Largest change, n = 0.015 | Largest change, n = 0.02 |
|---|---|---|---|---|---|
| Null | 0 | 0 | 10 of 10 | 0.15 cm | 0.15 cm |
| Random | 0 | 0 | 10 of 10 | 0.09 cm | 0.10 cm |
| Positive | 2 | 2 | 10 of 10 | 3.57 cm | 3.37 cm |

- Over the 10 receptor-patch pairs that change by 0.5 cm or more at either friction value: correlation 0.996, slope 0.94 (n = 0.02 against n = 0.015), same sign in all 10, largest difference 0.41 cm.
- Both patches with an effect of 1 cm or more have the same most-affected receptor at both friction values.
- Unchanged terrain: friction alone moves peak depth by a median of 0.03 cm, 95th percentile 0.56 cm, maximum 1.37 cm. One receptor crosses the 10 cm threshold (30 flooded at n = 0.015, 31 at n = 0.02).
- Limits: one storm, 30 patches, and only 2 of the 10 positives reach 1 cm at this storm, so the "same controlling ground" statement rests on few active cases. The comparison metrics were chosen after the runs; the plan fixed no pass line for this step.

**Do-no-harm check (plan step 3): cross-check agrees with the Air, not bit for bit.** Rerun here: harm-free design 5 receptors fall by 1 cm or more and 0 rise; naive design 3 fall and 7 rise (largest rise 1.3 cm). Same counts as the Air. Peak depths differ from the Air's file by up to 0.18 mm, so the M3 and M4 GPUs do not give identical floats. The Air's file stays at `results/pro/bet3_verify.npz`; this machine's is `results/pro/bet3_verify_pro.npz`.

**Bet 1 pilot (plan step 4): not run here.** The Air finished and scored it first, so I stopped my copy before it wrote any result.

**Bet 1 full run: started 18:14, forward order,** as `status/air.md` asks. Files go to `results/pro/bet1_full/` and are pushed every 10 minutes; `setup.npz` is left for the Air to commit.

**Other:** `docs/IPHONE_APP.md` is a task breakdown for a separate app agent. The human's Southwark station splat is in `data/scans/southwark_station/`; it is too blurred for centimetre heights.

## Sat 15:20: critical depths from the solver are done. Retest and non-triangular storms not yet run.

The human chose to follow the pivot as written after the 9 of 20 result. Two Air requests are outstanding and **not started**: the 12 retest cases in `shared/interventions_retest.npz` (about 8 minutes) and 8 non-triangular storms with time series.

**Task 5 result.** `results/pro/critical_*.npz`, one file per storm shape, 207 receptors.

| Shape | Receptors with a critical depth | Never flood up to the top depth | Critical net rain, 10th / median / 90th percentile | Documented site, total (net) |
|---|---|---|---|---|
| Front-loaded, 60 min | 53 | 154 | 11.1 / 33.5 / 92.0 mm | 25.9 (15.3) mm |
| Centred, 60 min | 53 | 154 | 11.1 / 29.3 / 86.6 mm | 26.2 (15.6) mm |
| Back-loaded, 60 min | 54 | 153 | 11.1 / 28.7 / 92.1 mm | 26.0 (15.4) mm |
| Centred, 30 min (to 60 mm only) | 39 | 166 | 11.9 / 21.1 / 50.2 mm | 20.8 (15.3) mm |

- **No receptor went from flooded back to dry as depth rose,** in any shape. The sweep is consistent with the order check.
- **Timing within the hour matters little for most receptors.** Front-loaded against back-loaded: median difference 0.4 mm of net rain, largest 15 mm.
- **In net rain, the documented site's critical depth is 15.3 to 15.6 mm in all four shapes.** The fill model put it at about 33 mm.
- 30 against 60 minutes, centred: median difference 0.5 mm of net rain over 39 receptors, largest 41 mm. A few receptors are strongly duration-dependent; most are not.
- Two receptors already flood at the lowest depth (10 mm) in the 30-minute shape, so they have no bracket there.
- Accuracy: the crossing is interpolated linearly inside a 4.8 mm bracket of total depth (3.3 mm for the 30-minute shape). Not a bisection to tolerance.

## Sat 14:45: GO/NO-GO RESULT. The solver confirms 9 of 20 predicted flips on peak depth, 11 of 20 on final depth. The kill line was 14.

Read this first. `solver/interventions.py`, results in `results/pro/interventions.npz`, 40 simulations, 730 s, mass imbalance at most 2.7e-5.

| Scoring | Confirmed |
|---|---|
| Flip as predicted, on peak depth (the definition of flooded) | **9 of 20** |
| Flip as predicted, on final depth | **11 of 20** |
| Depth at the target receptor moved in the predicted direction | **20 of 20** |
| Flips the solver did produce that went the predicted way | 9 of 9 |

By the kill line as written in `docs/PIVOT.md` (fewer than 14 of 20), this fails, on peak and on final depth. I have not rescored it any other way. What the failures look like:

- **Every one of the 11 failures is the solver being wetter than the fill model said.** In 8 cases the receptor was predicted dry before the change and the solver already had it flooded (peak 0.105 to 0.148 m). In 3 cases it was predicted dry after the change and stayed wet: two by a hair (0.100 and 0.102 m), one far off (case 19, 0.63 to 0.45 m). No case failed the other way.
- **The patch does what the fill model says to the water level.** The direction is right in all 20. Where the patch is at the receptor (12 cases) the peak moved a median 4.9 cm for a 5 cm change. Where it is 10 to 33 m away (8 cases) the peak moved a median 3.1 cm, from 0.4 to 15.5 cm, in the right direction every time.
- **So the controlling ground is identified correctly and the critical depth is placed wrongly.** The storms were set between the fill model's old and new critical depths. The solver's critical depths are lower, because the peak includes water in transit, so many storms were not between the solver's own before and after.
- By distance: patch at the receptor, 6 of 12 on peak and 7 of 12 on final. Patch 10 to 33 m away, 3 of 8 on peak and 4 of 8 on final.
- Side effects: in 2 cases one other receptor also changed state.

What I am not claiming: that rescoring on direction rescues the gate. It is a different, weaker test, chosen after seeing the result. A fair retest would place fresh storms using critical depths from the solver (task 5 below gives them for four storm shapes), on new cases, and count flips again.

**Decision for the human:** per `docs/PIVOT.md`, the entry continues only if the transit correction passes by Sat 20:00. The alternative reading of this result is a narrower claim: the fill model finds which few square metres control a building (20 of 20 on direction, including remote patches), but not the rain depth at which it floods.

## Sat 14:31: pivot tasks (`docs/PIVOT.md`)

| Task | State | Result |
|---|---|---|
| 1. Pilot committed, main run not launched | Done | `results/pro/bruteforce_pilot.npz`. I launched the 1,000-storm run at 14:09, a minute before pulling the pivot, and stopped it at once; nothing from it is kept. |
| 2. Receptor time series | **Done** | `results/pro/pilot_timeseries.npz` |
| 3. Intervention pairs | **Done: 9 of 20 on peak, below the kill line** | `results/pro/interventions.npz`, see above |
| 4. Order check | **Done: holds** | Larger storm at least as deep at every receptor, all 4 pairs |
| 5. Critical depths from the solver | **Done 15:15** | `results/pro/critical_*.npz` |

**Task 2, time series.** Pilot storms 0 to 15, depth at all 207 receptors every 30 s. Arrays: `depth` (16 x 159 x 207, m; NaN after a storm's own end), `t_s`, `t_end_s`, `storm_index`, `peak_depth`, `final_depth`.

- Peak depths are identical, bit for bit, to the pilot run. The solver is reproducible across batch sizes.
- **The 30 s samples miss the true peak by up to 1.6 cm.** Use `peak_depth` in the file for the peak, not the maximum of the series. Each sample is taken at the first step past its 30 s mark, so up to 1 s late.
- Mass imbalance at most 1.7e-5. 458 s for 16 storms.

**Task 4, order check: holds.** Four pilot storms (31, 60, 86, 108 mm) each against itself with every rain rate multiplied by 1.1, 1.2, 1.3, 1.2, same loss and same end time. `solver/pivot_runs.py order`, numbers in `results/pro/order_check.json`.

- **Peak depth at receptors:** the larger storm is deeper at all 207 receptors in all 4 pairs. Smallest margin +0.017 mm. No receptor flooded in the smaller storm and not in the larger.
- **Peak depth at any of the 262,144 cells:** the larger storm is lower by at most 0.13 mm, and by 1 mm or more nowhere.
- **Final depth:** lower in the larger storm by at most 0.03 mm at receptors. Over all cells, by at most 1.5 mm, in 2 cells of one pair. Final depth is a snapshot of water still moving, so it is not strictly ordered; the peak is, to float32 noise.
- What it means: "more rain at every instant gives at least as much peak water" held in every case, so a critical depth per receptor and storm shape is well defined, and one sweep over depth brackets every receptor at once.

**Task 5, critical depths.** `solver/critical_depth.py`. Four shapes, triangular as in `fill/make_shared.py`: front-loaded, centred and back-loaded at 60 minutes (24 depths, 10 to 120 mm) and centred at 30 minutes (16 depths, 10 to 60 mm, keeping the Air agent's 120 mm/h cap on mean intensity). The 0.10 m crossing is interpolated linearly in peak depth inside its bracket, so it is good to a fraction of the 4.8 mm (3.3 mm) grid spacing, not exact. Each file has `critical_depth_mm` and `critical_net_depth_mm` per receptor (NaN if it never floods or already floods at the lowest depth; flags say which), plus the full `peak_depth` grid.

**Task 3, intervention pairs.** The solver takes a different terrain per batch member, so unchanged and changed terrain run side by side. Air agent, what I need per case: the rain profile (60 rates in mm/h at 60 s, or an index into a storm file), `loss_mm_h`, `duration_s`, the receptor index, and the terrain change as cell rows, cell columns and height changes in metres. Any layout carrying those is fine; say which in `status/air.md`.

## Where things stand

| Gate | State | Number |
|---|---|---|
| Sat 16:00 throughput | **Passed** | 710M cell-steps/s single storm, 470M batched (bare update). 283M for the full solver on the shared terrain, batch of 8. |
| Sat 20:00 checks 1 to 3 | **Passed** | JAX agreement 2.4e-6 m; mass imbalance at most 1.5e-5; lake at rest moves 0. |
| Sat 20:00 check 5 | **Reported** | 1 m and 2 m agree on 96.8% of flooded-or-not decisions (above the 95% line). |
| Check 4 (analytic case) | **Reported, with a limitation** | Wave front within 0.1% at n = 0.1, 2.4% late at n = 0.03, 7% late at n = 0.01. Model error, not a time-step error. |
| Sat 22:00 pilot | **Done 14:08** | `results/pro/bruteforce_pilot.npz`: 64 storms, 1,317 s, 20.6 s per storm, mass imbalance at most 2.2e-5. |
| Sat 23:30 main run | **Cancelled by the pivot** | Measured cost if wanted later: 20.6 s per storm, 5.7 h for 1,000. |

Now using `shared/terrain_512.npz`, `shared/receptors.npz` and `shared/storms_*.npz`. Rain goes on `open` cells at `max(profile - loss, 0)`, as `status/air.md` asks. Roof rain is not added.

## Pilot (done)

`results/pro/bruteforce_pilot.npz`, all 64 storms in `shared/storms_pilot.npz`, 207 receptors.

- **Wall-clock:** 1,317 s for 64 storms, 20.6 s per storm (14.7 to 25.7 by chunk), 268M cell-steps/s. Slower than the 283M in the checks because another job (`emulator/`, not mine) was using the CPU for part of it.
- **Mass balance:** imbalance at most 2.2e-5 of net rain across all 64.
- **Flooded cases:** 2,253 of 13,248 storm-receptor pairs reach 0.10 m. 54 receptors flood in at least one storm; 153 never do.
- Deepest water 0.39 to 2.31 m; 8,575 to 28,864 steps per storm.

## Gate 1: throughput (passed)

Bare core update, `scripts/bench_step.py mlx B 512 300`, synthetic terrain:

| Batch | Mcell-steps/s |
|---|---|
| 1 | 710 |
| 8 | 485 |
| 32 | 470 |
| 64 | 467 |

Batching does not raise throughput per cell: one 512 x 512 storm already saturates the GPU. This matters for the pitch. On this hardware the ensemble is not faster per storm when batched, so the only way to cut wall-clock is to simulate fewer storms, which is what the cascade does.

Full solver on the shared terrain, 8 pilot storms together: **283M cell-steps/s**, 164 s wall, 10,400 to 26,100 steps per storm. That figure counts only steps on storms still running.

## Correctness checks

Reproduce with `uv run --with mlx --with numpy --with jax --with scipy python solver/checks.py`. Raw numbers in `results/pro/checks.json`.

**Check 1, agreement with the JAX reference: passed.** Synthetic street 1 from `prior/floodlab.py` at 0.25 m, 60 mm in 2 minutes, 300 s, gullies off in both.

| Run | Largest difference in final depth, any cell | Largest difference in peak door depth |
|---|---|---|
| Same fixed time step as the reference (5,000 steps) | 0.0024 mm | 0.24 mm |
| My adaptive time step (2,299 steps) | 1.2 mm | 0.15 mm |

Reference peak door depths are 6.0, 6.8 and 6.7 cm at the three wet doors. The 0.24 mm peak figure compares my mean of per-cell peaks with the reference's peak of the door mean, so it is not quite the same quantity.

**Check 2, mass balance on the real terrain: passed.** 8 pilot storms from 16 to 112 mm. Net rain 1,296 to 17,137 m3. Rain in minus water stored minus water out through the edge: at most **1.5e-5** of rain in. At 2 m: 4.7e-6. The drainage loss never enters the grid, so it needs no balance term.

**Check 3, lake at rest: passed.** Still water at 3.0 m AOD (25,554 wet cells, up to 2.07 m deep) and at 4.0 m AOD (123,387 wet cells), edge outflow off, 600 s: no cell changed depth at all in float32.

**Check 5, resolution: 96.8% agreement.** The same 8 storms at 1 m and at 2 m, 193 receptors (14 dropped because their 2 m cell is mostly building), 1,544 cases.

- Flooded at 1 m: 241. Flooded at 2 m: 226. Flooded at 1 m only: 32. Flooded at 2 m only: 17.
- Per-storm agreement 95.3% to 100%.
- Peak depth difference: median 1.3 mm, 95th percentile 4.2 cm.
- The 2 m run took 24 s against 164 s.

What it means: the flood table depends a little on resolution, about 3% of decisions, and those sit near the threshold. That is the same population the band is meant to catch. Limitation to state: 2 m coarsening here is my own (a coarse cell is open if 2 or more of its 4 cells are open; height is the mean of its open cells).

**Check 4, analytic case: scheme converges, and shows the known limit of the local-inertial model.** A wave advancing at 1 m/s over a flat plane for one hour (the test in Bates et al. 2010, after Hunter 2005; recalled from memory, source not re-read). Exact front at 3,600 m. `solver/checks.py 4`.

| Manning n | Deepest water | Front at dx = 50, 25, 10 m | Depth error (RMSE) at 10 m |
|---|---|---|---|
| 0.10 | 6.7 m | 3,725, 3,663, 3,605 m | 4.1 cm |
| 0.03 | 2.4 m | 3,625, 3,563, 3,515 m | 6.6 cm |
| 0.01 | 0.93 m | 3,425, 3,363, 3,335 m | 6.1 cm |

- At high friction the front converges on the exact position as the grid refines.
- At low friction the front settles 2.4% (n = 0.03) and 7% (n = 0.01) behind. Cutting the time step by 3.5 times changed nothing past the fourth digit, so this is not a time-step error. The local-inertial equations drop the advection term, and the exact solution needs it when friction is weak. My reading, not checked against the paper: this is the lag the literature reports for this scheme at low friction.
- **Limitation for our run:** we use n = 0.015, the low-friction end. Fast, deep flow arrives a few percent late in this solver compared with full shallow water. Ponded depths are unaffected (checks 2 and 3). Both the brute-force table and the cascade use the same solver, so the comparison between them is not affected; the absolute flood timing is.

## Solver, as built

`solver/flood.py`, `simulate(...)`. `solver/run.py` wraps it for storm sets.

- Local-inertial scheme (Bates et al. 2010) with semi-implicit Manning friction and a flux limiter that stops a cell giving more water than it holds. Same update as `prior/floodlab.py`.
- **Time step.** Per storm, `dt = 0.7 * dx / sqrt(g * hmax)`, with `hmax` that storm's deepest water, refreshed every 10 steps. Capped at 1.0 s (the value for 5 cm of water). Each storm in a batch has its own `dt` and clock; a finished storm gets `dt = 0`, which freezes it exactly. The run aborts on any non-finite depth.
- **32-bit.** MLX on the Apple GPU has no float64. Rain volume and edge outflow are summed on the host in float64 from the float32 values the GPU used. Mass balance above shows this is adequate.
- **Outputs.** Peak and final depth at every receptor, mass balance terms, steps, deepest water. The runner also keeps full peak-depth maps locally (`results/pro/fields_*`, not committed), so receptors can be moved without a rerun.

**For the Air agent, Sunday:** `from run import run_storms` (in `solver/`), then `run_storms("shared/storms_main.npz", indices)` returns `peak_depth`, `final_depth`, `storm_index`, `wall_s` for any subset.

## The pits set the cost

The deepest water is 2.1 to 2.3 m in every storm above about 30 mm, and 0.88 m at 16 mm. Those are the rectangular pits the Air agent noted at rows 190 to 230. The time step is set by the deepest water anywhere, so those pits hold `dt` near 0.15 s for the whole domain. Without them the deepest water would be well under 1 m and the run would be roughly 1.5 to 2 times faster. I have not changed the terrain; it is the Air agent's call and the fill model must see the same ground.

## Assumptions

- **Rain on roofs** is not added to the ground (matches `status/air.md`: roofs drain to sewers). Lowers flooding.
- **Drainage loss** is subtracted from the rain rate, floored at zero. Water already ponded is not drained after the rain stops. The brief defines the loss as "removed from rainfall".
- **Buildings** hold no water and pass no flow, by masking faces. Their 20 m raised height is not used.
- **Boundary:** critical-depth outflow at every open cell on the domain edge. Nothing flows in from outside the 512 m tile, so upstream run-on is ignored.
- **Manning n = 0.015** everywhere (smooth asphalt), carried over from the prior code. Not calibrated.
- **No flux smoothing** (de Almeida 2012 theta = 1). The option exists; the plain scheme has stayed stable and mass-conserving in every run so far.
- **Rain rate is read at the start of each step**, so a change in the 60 s profile lands up to one step (at most 1 s) late. The mass accounting uses the same value.
- **Storms that end early keep their batch slot.** Batches are sorted by duration to limit the waste. Wall-clock per storm is the chunk's wall-clock shared equally.

## Next

1. Critical-depth sweep finishes; commit.
2. Intervention pairs as soon as `shared/interventions.npz` lands (they take priority over the sweep).

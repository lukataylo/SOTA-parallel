# Status: MacBook Pro M3 agent

Last updated: Sat 21 Nov, 14:10. Machine: MacBook Pro M3 Pro (Mac15,6), 36 GB, MLX on the Apple GPU.

## Where things stand

| Gate | State | Number |
|---|---|---|
| Sat 16:00 throughput | **Passed** | 710M cell-steps/s single storm, 470M batched (bare update). 283M for the full solver on the shared terrain, batch of 8. |
| Sat 20:00 checks 1 to 3 | **Passed** | JAX agreement 2.4e-6 m; mass imbalance at most 1.5e-5; lake at rest moves 0. |
| Sat 20:00 check 5 | **Reported** | 1 m and 2 m agree on 96.8% of flooded-or-not decisions (above the 95% line). |
| Check 4 (analytic case) | **Reported, with a limitation** | Wave front within 0.1% at n = 0.1, 2.4% late at n = 0.03, 7% late at n = 0.01. Model error, not a time-step error. |
| Sat 22:00 pilot | **Done 14:08** | `results/pro/bruteforce_pilot.npz`: 64 storms, 1,317 s, 20.6 s per storm, mass imbalance at most 2.2e-5. |
| Sat 23:30 main run | **Launched 14:09** | 1,000 storms at 1 m, 125 chunks of 8. Forecast 5.7 h, so about 20:00. Log: `results/pro/main.log`. |

Now using `shared/terrain_512.npz`, `shared/receptors.npz` and `shared/storms_*.npz`. Rain goes on `open` cells at `max(profile - loss, 0)`, as `status/air.md` asks. Roof rain is not added.

## Pilot (done)

`results/pro/bruteforce_pilot.npz`, all 64 storms in `shared/storms_pilot.npz`, 207 receptors.

- **Wall-clock:** 1,317 s for 64 storms, 20.6 s per storm (14.7 to 25.7 by chunk), 268M cell-steps/s. Slower than the 283M in the checks because another job (`emulator/`, not mine) was using the CPU for part of it.
- **Mass balance:** imbalance at most 2.2e-5 of net rain across all 64.
- **Flooded cases:** 2,253 of 13,248 storm-receptor pairs reach 0.10 m. 54 receptors flood in at least one storm; 153 never do.
- Deepest water 0.39 to 2.31 m; 8,575 to 28,864 steps per storm.

## Main run (in progress)

Launched 14:09 on `shared/storms_main.npz`: all 1,000 storms, 1 m, batches of 8 sorted by duration. Nothing was reduced.

- Resume after a crash by rerunning the same command: `caffeinate -is uv run --with mlx --with numpy python -u solver/run.py shared/storms_main.npz main 8`. Finished chunks in `results/pro/chunks_main/` are reused.
- **Timing caveat.** The `emulator/` job was still running on this machine at launch. If it keeps running, the baseline wall-clock is inflated. I will re-time a few chunks on a quiet machine afterwards and report both figures; the per-chunk `wall_s` in the results is whatever was measured.

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

1. Watch the main run; commit chunks as they land.
2. Re-time a few chunks on a quiet machine for a clean baseline figure.
3. Solver speed, only after the main run so the timing is not disturbed.

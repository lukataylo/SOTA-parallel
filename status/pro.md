# Status: MacBook Pro M3 agent

Last updated: Sat 21 Nov, 13:55. Machine: MacBook Pro M3 Pro (Mac15,6), 36 GB, MLX on the Apple GPU.

## Where things stand

| Gate | State | Number |
|---|---|---|
| Sat 16:00 throughput | **Passed** | 710M cell-steps/s single storm, 470M batched (bare update). 293M for the full solver on real terrain, batch of 8. |
| Sat 20:00 checks 1 to 3, check 5 | In progress | Mass balance on real terrain already at 1e-5 or better (below). |
| Sat 22:00 pilot | Waiting on `shared/` | |
| Sat 23:30 main run | Not started | Estimate: about 19 s per storm, so 1,000 storms is about 5.3 h. |

## Gate 1: throughput (passed)

Bare core update, `scripts/bench_step.py mlx B 512 300`, synthetic terrain:

| Batch | Mcell-steps/s |
|---|---|
| 1 | 710 |
| 8 | 485 |
| 32 | 470 |
| 64 | 467 |

Batching does not raise throughput per cell: one 512 x 512 storm already saturates the GPU. Batching is still how the run is organised, but it buys nothing per cell-step.

Full solver (`solver/flood.py`: walls, per-storm rain, outflow, peak field, mass accounting) on the real tile, 8 stand-in storms run together: **293M cell-steps/s**, 152 s wall for 8 storms. That counts only steps on storms still running; a storm that ends early keeps occupying its batch slot. Sorting storms by expected length before batching is the next speed item.

What it means: the main run is feasible at 1 m with about 1,000 storms. No need to drop to 2 m.

## Solver, as built

`solver/flood.py`, function `simulate(z, open, dx, rc, profile, profile_dt_s, loss_mm_h, t_end_s, ...)`.

- Local-inertial scheme (Bates et al. 2010) with semi-implicit Manning friction and a flux limiter that stops a cell giving more water than it holds. Same update as `prior/floodlab.py`.
- **Time step.** Per storm, `dt = 0.7 * dx / sqrt(g * hmax)`, where `hmax` is that storm's deepest water, refreshed every 10 steps. Capped at 1.0 s (the value for 5 cm of water). Each storm in a batch has its own `dt` and its own clock; a finished storm gets `dt = 0`, which freezes it exactly.
- **Terrain oddity that sets the cost.** Some open cell ponds to 2.1 to 2.4 m in every stand-in storm, even 26 mm. That pit forces `dt` down to about 0.15 s for the whole domain. Air agent: when you build `shared/terrain_512.npz`, look for a deep pit on open ground (the DTM minimum is -0.43 m AOD). If it is an artefact and you fill it, the solver gets several times faster. I will locate it and report the cell.
- **32-bit.** MLX on the Apple GPU has no float64. Rain volume and boundary outflow are summed on the host in float64 from the float32 values the GPU used.

Mass balance on the real tile, 8 stand-in storms, 26 to 115 mm: imbalance between -6.0e-6 and +8.3e-6 of net rain. 

## Assumptions (all provisional until the shared files exist)

- **Rain on roofs:** currently dropped (`rain_mult=1.0`, rain falls on open cells only). The brief says add it to open ground; uniform redistribution is `rain_mult = 1 / open fraction = 1.53`. One parameter. Air agent: say in `status/air.md` which you assume in the fill model and I will match it.
- **Drainage loss** is subtracted from the rain rate, floored at zero. It never enters the grid, so water already ponded is not drained after the rain stops. Justification: the brief defines it as "removed from rainfall".
- **Buildings** hold no water and pass no flow (face masks), so their terrain height is irrelevant to the solver.
- **Boundary:** critical-depth outflow at every open cell on the domain edge.
- **Manning n = 0.015** everywhere (smooth asphalt), carried over from the prior code. Not calibrated.
- **Storm profile format I expect:** `profile` as storms x K in mm/h plus a scalar step in seconds. The contract does not name the step; please store it as `profile_dt_s`.
- Stand-in storms: `standin_storms()` in `solver/flood.py`, brief ranges, Gaussian-bump profiles.

## Next

1. Checks 1 to 3 (JAX agreement, mass balance, lake at rest), then 5 (1 m against 2 m).
2. Find the deep pit.
3. Chunked, resumable batch runner for the pilot and main run.

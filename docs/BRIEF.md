# Shared brief: "Time-step only where it matters"

Read this first, then your own brief: `BRIEF_PRO.md` (MacBook Pro M3) or `BRIEF_AIR.md` (MacBook Air M4).

## What we are entering

The SoTA Scientific Parallelism Hackathon ends **Sunday 22 November, 18:00**. The judging criteria are in the top-level `README.md`. One of the organisers' example challenges is flood uncertainty: simulate thousands of rainfall scenarios to estimate flood risk.

Our entry is a two-step flood ensemble on real London terrain:

1. **Fill step.** A fast fill-and-overflow model gives the settled water depth at every receptor for every storm. It needs no time-stepping.
2. **Band.** Storms where a receptor's fill depth is close to the flooding threshold are "undecided". The band's width is measured against the simulator, on both sides.
3. **Simulator step.** The time-stepping shallow-water solver runs only on undecided storms.

The claim we want to test: for N storms, the cascade produces the same per-receptor flood table as simulating every storm, in X times less wall-clock on the same machine, with a measured count of missed floods.

The baseline is the same solver, batched, on the same machine, run over every storm. That run is also the ground truth.

A storm is skipped only when **every** receptor is decided, because the solver simulates the whole domain. So the number that matters is the fraction of storms with no receptor in the band. Nobody has measured it on real terrain. If it is small, we pitch the negative result with its mechanism, which the judges explicitly reward.

## What is already known

All earlier results are from synthetic 32 m streets on two CPU cores. `prior/SUMMARY.md` has the detail and `prior/` has the code.

- **The solver works.** `prior/floodlab.py` is a JAX local-inertial solver that conserves mass and has checked gradients.
- **The volume bound held on synthetic streets.** A door stays dry if the rain that can reach it cannot fill the ground around it to the threshold: 0 misses in 640 cases after one repair. On real terrain the bound must count the whole upstream catchment, and its coverage is unknown.
- **Still water underestimates moving water.** "A still pond can never reach this door" failed in 190 of 462 cases. No failures occurred where the threshold cleared the still level by more than 12 cm in validation (0 of 86), with 1 of 62 in an earlier batch. This is why the band exists and why it must be two-sided.
- **Full fill is exact; partial fill is unbuilt.** The fill level for unlimited rain matches sequential priority-flood on terrains up to 1M cells. A storm that stops partway is not handled yet.
- **Hardware.** There is no cloud GPU. On the M4 Air the solver's core update runs at about 105M cell-steps/s on CPU (JAX) and 340 to 450M on the Apple GPU (MLX). `scripts/bench_step.py` reproduces this. The M3 Pro is unmeasured.

## The shared contract

Both agents depend on these files. The Air agent writes them first and does not change their format afterwards without telling the Pro agent in `status/air.md`.

| File | Written by | Contents |
|---|---|---|
| `shared/terrain_512.npz` | Air | `z` (512 x 512 float32, simulation terrain with buildings raised as walls), `open` (bool, cells that receive rain and hold water), `dx` |
| `shared/receptors.npz` | Air | `rc` (n x 2 int, row and column of each receptor cell), `threshold_m` (scalar depth that counts as flooded), `label` (strings; includes the documented flood site) |
| `shared/storms_pilot.npz`, `shared/storms_main.npz` | Air | per storm: `depth_mm`, `duration_s`, `profile` (rain-rate time series at fixed step, mm/h), `loss_mm_h` (drainage loss), `seed` |
| `results/pro/bruteforce_*.npz` | Pro | `peak_depth` (storms x receptors, m), `final_depth` (same shape), `storm_index`, `wall_s` per chunk, solver settings |
| `results/air/fill_*.npz` | Air | `fill_depth` (storms x receptors, m), `wall_s` |

"Flooded" means peak water depth at the receptor cell reaches `threshold_m` at any time in the simulation.

Until the shared files exist, the Pro agent works from `data/blackfriars_512.npz` with its own stand-in storms.

## Rules for both agents

- **Stay in your own directories.** Pro owns `solver/`, `results/pro/`, `status/pro.md`. Air owns `fill/`, `shared/`, `results/air/`, `status/air.md`. Either may read anything.
- **Commit small and often to `main`.** Run `git pull --rebase` before every push. Never force-push. Never commit `.env` or `data/raw/`.
- **Keep your status file current.** Each time a gate is passed or failed, write the measured numbers, what they mean, and what you are doing next. The other agent and the human read this file, so write it for someone arriving cold.
- **Every simplifying assumption gets written down** in your status file with a one-line justification. The judges score this directly.
- **Report what you measured.** A failed gate is a result. Do not tune a threshold after seeing a failure and present it as a pass; if you repair something, say so and re-test on fresh cases.
- **Wording.** Do not write "certified" or "guaranteed". The bound is a conservative screen with a measured miss rate.
- **Use `uv run --with ...`** for Python dependencies. Do not install anything globally.
- **Stop and write to your status file** if you hit something that changes the plan for the other agent: a format change, a gate failure, a physical oddity in the terrain.

## Assumptions to state, and to confirm with a mentor

These are working defaults from memory, not checked values. Mark them as assumptions wherever they appear.

- **Storms.** Total depth 10 to 120 mm, duration 15 to 60 minutes, three temporal profiles (front-loaded, centred, back-loaded). The simulation runs for the storm duration plus 20 minutes.
- **Drainage loss.** A constant 12 mm/h removed from rainfall to stand in for sewers.
- **Buildings.** Treated as walls. Rain falling on roofs is added to the open ground (state which way you handled it).
- **Flooded threshold.** 0.10 m depth at the receptor cell.
- **Boundary.** Water leaves freely at the domain edge.

## Timeline and gates

| When | Gate | Owner |
|---|---|---|
| Sat 15:30 | Shared terrain, receptors and pilot storms committed | Air |
| Sat 16:00 | Solver throughput measured on the M3 Pro, single and batched | Pro |
| Sat 16:30 | Volume-bound coverage on the real tile reported | Air |
| Sat 19:00 | Partial fill matches its oracle on at least 98% of decisions, or we fall back to the volume screen alone | Air |
| Sat 20:00 | Solver checks pass on real terrain; 1 m against 2 m compared | Pro |
| Sat 22:00 | 64-storm pilot through both steps; band set from it; fraction of undecided storms known | both |
| Sat 23:30 | Main brute-force run launched, sized to finish by Sun 07:00 | Pro |
| Sun 09:00 | Misses, storms skipped and wall-clock scored for both routes | Air |
| Sun 11:00 | Pitch decided: speedup, or negative result | human |

## The three numbers the final slide needs

1. **Speedup:** end-to-end wall-clock for the same flood table, cascade against brute force, same machine.
2. **Soundness:** missed floods out of N held-out storm-receptor cases, and the band width in cm on real terrain.
3. **Science:** the critical storm at the documented flood site on Blackfriars Road, and whether it fits the record.

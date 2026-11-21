# Flood emulator training experiments: summary

Session of Sat 21 Nov 2026, about 3 h 15 min wall-clock. Everything here is on a 48 x 48 toy grid at 10 m.
**Toy grids are not real streets.** The one real-terrain check (`T_real`, below) is where every emulator does worst.

Read this first:

- **Six of ten experiments have a result.** E1, E2, E3, E10 ran in full with 3 seeds. E5 is partial. E4, E6, E7, E8, E9 are NOT RUN (code written and smoke-tested, no results).
- **No GPU rule not applied in the end.** The solver runs on CPU (JAX has no supported Apple-GPU backend). Emulators trained on the Apple GPU (MPS), shared with another job. Grid is 48 x 48; dataset sizes are the brief's full sizes for B3, E2, E1.
- **Config in every result:** rainfall cap 150 mm/h peak, fixed volume 30 mm per storm (60 mm/h mean over 30 min), 40 min simulated, sewer sink 10 mm/h, Manning n 0.015.
- Every number below is **measured** unless marked *derived* or *assumed*.

## Harness checks (run before anything else)

| Check | Result |
|---|---|
| Mass conservation, float64, four terrain kinds | imbalance at most 3.3e-14 of rainfall |
| Mass conservation, float32 production runs, all test sets | at most 3.4e-5 of rainfall |
| Lake at rest over uneven ground, 100 steps | 1.8e-15 m movement |
| Gradient of depth w.r.t. storm, autodiff vs central finite difference | relative error 1.0e-4 (eps 1e-3) to 1.8e-3 (eps 1e-5) |
| Storm constraints | volume within 0.1% of 30 mm; peak never above 150 mm/h |
| Gradient search vs best of 1,024 random storms, one terrain, equal volume, under the cap | 1.27 m vs 0.99 m at the target cell (random median 0.86 m) |
| Gradient search, mean over 64 terrains | 0.52 m at start, 0.73 m after 25 steps |

The earlier figure (0.58 m against 0.33 m) was on a different terrain and without the cap, so only the direction is comparable.

## Result table

Peak-depth RMSE in metres, median of 3 seeds. Full table with all six metrics per test set, ranges, and `T_real`: `results/table.md`.

| Row | T_iid RMSE | T_iid tail RMSE | T_tail RMSE | T_terrain RMSE | T_iid mass err | CPU s/storm (b256) | x vs B0 | x vs B1, CPU | x vs B1, GPU emulator | Labels | Train s | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 solver, single storm | 0 | 0 | 0 | 0 | 3e-5 | 0.0867 (b1) | 1 | | | | | reference |
| B1 solver, batch 256 | 0 | 0 | 0 | 0 | 3e-5 | 0.0248 | 3.5 | 1 | | | | reference |
| B2 coarse solver + upsample | 0.0401 | 0.230 | 0.0450 | 0.0353 | 0.057 | 0.00050 | 47 | 49 | | 0 | 0 | baseline |
| B3 U-Net 2M | 0.0109 | 0.037 | 0.0209 | 0.0336 | 0.021 | 0.0082 | 14 | 3.0 | 51 | 2,000 | 570 | baseline |
| E1 adversarial active learning | 0.0125 | 0.045 | **0.0235** | 0.0290 | 0.027 | 0.0116 *derived* | 9.8 | 2.1 | 37 | 1,200 | 371 | PASS |
| E1 control (random) | 0.0122 | 0.045 | 0.0258 | 0.0278 | 0.026 | 0.0116 *derived* | 9.8 | 2.1 | 37 | 1,200 | 453 | control |
| E2 multi-terrain | 0.0115 | 0.039 | 0.0219 | 0.0328 | 0.023 | 0.0082 | 14 | 3.0 | 51 | 4,096 | 246 to 737 | FAIL |
| E2 + curriculum | 0.0114 | 0.038 | 0.0220 | 0.0333 | 0.022 | 0.0082 | 14 | 3.0 | 51 | 4,096 | 736 | FAIL |
| E3 solver-in-the-loop corrector | 0.0410 | 0.250 | 0.0465 | 0.0363 | 0.045 | 0.0031 | 21 | 8.1 | | 2,000 | 680 | FAIL |
| E4 residual diffusion | | | | | | | | | | | | NOT RUN |
| E5 pretrained operator | 0.0187 (100 labels) | | | | | | | | | 100 + 2,730 pretrain | | BLOCKED (Poseidon); fallback incomplete |
| E6 in-context operator | | | | | | | | | | | | NOT RUN |
| E7 CRPS ensemble | | | | | | | | | | | | NOT RUN |
| E8 multi-fidelity | | | | | | | | | | | | NOT RUN |
| E9 amortised inversion | | | | | | | | | | | | NOT RUN |
| E10 distillation (own site test) | 0.0056 student vs 0.0063 teacher | | | | | 0.0029 | | | | 50 solver + 950 teacher | | FAIL (accuracy met, speed 2.8x < 5x) |

Timing notes:

- Hardware: Apple M3 Pro (6P+6E cores, 36 GB), shared with another job throughout.
- The CPU columns are like for like: solver and emulator both on CPU, emulator on one thread, batch 256 (B0 column: batch 1).
- The GPU column puts the emulator on the Apple GPU against the CPU solver. That is not like for like, and there is no GPU solver number here to compare against.
- Timings were taken while two leftover jobs were still winding down, so treat them as good to about 20%.
- "x vs B0" uses batch 1 for both; "x vs B1" uses batch 256 for both. B1 is the 4-process pool of vmapped chunks (223M cell-steps/s); in-process vmap is 161M; single storm 64M.
- E2 train time has a wide range because runs shared the GPU. E1 rows time four small networks, derived from the single-network timing.

## What happened, why, what it means

**B2 and the resolution floor.** The 4x-coarse solver costs 0.5 ms per storm and gives 0.040 m RMSE. Block-averaging the *true* fine answer to 12 x 12 and upsampling it gives 0.0387 m. So any method whose output lives on the coarse grid can improve on B2 by 3.5% at most on `T_iid`.

**B3.** The plain 2M U-Net reaches 0.0109 m on `T_iid` and holds up on the search-built tail set (0.0209 m), but on unseen street terrain it is no better than the coarse solver (0.0336 vs 0.0353 m). It needed two fixes chosen on the validation split: GroupNorm (without it one seed in three stalled near the predict-zero loss) and learning rate 1e-3. On one CPU thread it is only 3.0x faster than the batched solver.

**E1, adversarial active learning: PASS.** At 1,200 labels the adversarial arm beats the random arm on `T_tail` in all three seeds, 0.0235 m [0.0223 to 0.0238] against 0.0258 m [0.0255 to 0.0263]. Ensemble disagreement tracked true error after round 1 (Spearman 0.71 to 0.76, kill line 0.2). The cost is a slightly worse `T_iid` (0.0125 vs 0.0122 m), and neither arm beats B3 on `T_iid` or `T_tail`; both beat B3 on `T_terrain` (0.029 and 0.028 vs 0.034 m), which counts as the "beats B3 on one set" win. Leakage check: the acquired storms were found on fresh terrains by a different objective than the one that built `T_tail`.

**E2, terrain randomisation and curriculum: FAIL.** Pass needed `T_terrain` RMSE within 2x of `T_iid`; it is 2.9x (0.0328 vs 0.0115 m), and the gain over B3 on streets (0.0328 vs 0.0336 m) is inside the seed range. Training on three kinds does generalise *within* those kinds, where B3 does not:

| Test kind | B3 (fractal only) | E2 | E2 + curriculum |
|---|---|---|---|
| fractal | 0.0109 | 0.0115 | 0.0114 |
| valley | 0.0206 | 0.0087 | 0.0086 |
| basin | 0.0194 | 0.0071 | 0.0070 |
| street (held out) | 0.0336 | 0.0328 | 0.0333 |

The curriculum made no measurable difference: it cleared all three easier levels within the first 415 of 3,840 steps, so it barely changed what the network saw. The meaning: more terrains of the kinds you have do not buy transfer to a kind with different structure (kerbs, building blocks).

**E3, solver-in-the-loop corrector: FAIL.** It did not beat B2 on any test set (0.0410 vs 0.0401 m on `T_iid`) and improved mass error only on `T_iid` (0.045 vs 0.057). Training was stable at every unroll length (8, 32, and a full-length 40 stage I added), so the kill condition did not trigger. The reason is the floor above: the corrected field is still 12 x 12, and the error is almost all sub-grid ponding that no coarse field can hold. A corrector needs a fine-grid output head to have any room.

**E5, pretrained operator: BLOCKED, fallback incomplete.** Poseidon-T is reachable (HTTP 200) but was not downloaded or run; wiring in its code and fine-tuning it did not fit the session. The fallback (small U-Net pretrained on valley and basin terrains, fine-tuned on fractal labels) was killed by my own stray `pkill` before it saved, so only `T_iid` RMSE from the log survives: fine-tuned 0.0217 / 0.0187 m at 20 / 100 labels against 0.035 / 0.0215 m from scratch (3 seeds), and 0.0162 vs 0.0184 m at 500 labels (1 seed). Pretraining helps most at 20 labels, but nothing matches B3's 0.0109 m with 10x fewer labels, so the pass condition is not met on the evidence there is. Arms B and C were not run: the emulators output peak and final depth, not a time-resolved state, so there is no equation residual to take.

**E10, distillation: FAIL on speed, accuracy met.** On one fractal site, the 0.12M-parameter student trained on teacher outputs plus 50 solver labels beats its 1.95M-parameter teacher: 0.0056 m [0.0053 to 0.0058] against 0.0063 m. It is 2.8x faster on CPU (2.9x on GPU), short of the 5x required. Uncertainty-picked labels did *worse* than random ones (ratio to teacher 0.88 vs 0.83), and with no solver labels the student simply matches the teacher (1.01). So a handful of solver labels matters, picking them by teacher disagreement does not, and a 16x smaller network is not 16x faster at this size.

**E4, E6, E7, E8, E9: NOT RUN.** The scripts exist and their pieces passed a smoke test, but there are no results. E8 was started and stopped before any arm completed. E9 simulated its 21,000 storms and was stopped at epoch 5 of 20. E7 was killed by the same stray `pkill` as E5. E4 and E6 were never started.

## Real terrain (`T_real`, not blocked)

Environment Agency LIDAR Composite 2022 at Blackfriars Road, Southwark, block-averaged from 1 m to 10 m, buildings raised 3 m, 256 random storms. Mean of per-storm maximum depth is 1.42 m, against 0.57 m on `T_iid`.

| Row | RMSE all (m) | Tail RMSE (m) | CSI at 0.1 m |
|---|---|---|---|
| B2 coarse solver | 0.075 | 0.49 | 0.06 |
| B3 | 0.082 | 0.47 | 0.15 |
| E2 | 0.075 | 0.42 | 0.17 |
| E2 + curriculum | 0.078 | 0.43 | 0.17 |

Every emulator is about 7x worse here than on `T_iid` and none clearly beats the coarse solver on RMSE. Nothing trained on these procedural terrains should be trusted on a real street.

## Figures

- `results/failure_map.png`: B3 across terrain roughness and storm intensity. Error rises steadily with roughness (0.003 m at roughness 0.1 to 0.019 m at 1.4, which is outside the training range) and is flat across storm concentration. Terrain, not rainfall, is what breaks it.
- `results/speedup.png`: `T_iid` RMSE against CPU seconds per storm for B2, B3, E1, E2, E3.
- `results/<experiment>/examples.png`: solver, prediction and error map for three test storms (B2, B3, E1, E1_control, E2, E2_curriculum, E3, E10).

## Recommendation

1. **E1, adversarial active learning.** It is the only clean pass. *Scientific value:* a measured tail gain at equal label count, 3 seeds, non-overlapping ranges. *Reshaping:* the search for hard storms runs as one batched gradient ascent through the emulators, and labelling is one vmapped solver call. *Correctness:* every acquired storm is re-projected under the cap and labelled by the fine solver. *Speedup:* weak, as for every emulator here.
2. **The coarse solver (B2) as the fast path, with a fine-grid learned corrector as the next experiment.** *Speedup:* 49x over the batched fine solver on the same CPU, with no training and no labels. *Correctness:* it is the same physics, and its error is explained (the 12 x 12 floor). *Scientific value:* E3 and the floor measurement say exactly what to build next: a correction that outputs on the fine grid, conditioned on fine terrain (the E4 idea, untested).

The honest speedup finding: on this grid the batched solver already does 223M cell-steps/s on CPU, so a 2M U-Net buys 3x on the same hardware and 51x only by moving the emulator to a GPU the solver is not using. That gap should widen on larger grids, which was not tested.

## Simplifying assumptions

| Assumption | Justification | Kind |
|---|---|---|
| Solver is `prior/floodlab.py`'s scheme with rain as a space-time field, a uniform sewer sink, outflow on one edge | Brief's spec; physics of the step unchanged; mass, lake-at-rest and gradient re-verified | measured |
| 48 x 48 at 10 m, dt 1 s fixed | Matches the earlier toy grid; CFL 0.7 holds to about 5 m depth; fixed dt keeps jit/vmap/checkpointing | assumed |
| Storm = 8 time slabs x 6 x 6 knots, bilinear in space, constant within a slab | Low-dimensional, so cap and volume hold exactly and search has 288 parameters | assumed |
| 30 mm in 30 min, 150 mm/h cap, 10 mm/h sink, Manning 0.015 | Cap is the brief's default; the rest are working values, not checked against design-storm tables | assumed |
| Emulators predict peak and final depth only | Brief's metrics need only these; it rules out equation-residual training (E5 B/C) | assumed |
| Emulator mass error = final-depth volume against the solver's rain minus outflow minus drainage | Peak depth is not a state at one time, so volume is checked on the final field | assumed |
| `T_terrain` holds out one kind (street); train kinds are fractal, valley, basin | Basins are named in the E2 curriculum, so they must be in training | assumed |
| `T_tail` is 64 searches x 4 harvested iterates, not 256 independent searches | Search cost; iterates of one search share a terrain and are correlated | assumed |
| B3 and E2 use a fresh terrain per storm, terrain as an input channel | Lets one network be scored on every test set | assumed |
| Three seeds vary initialisation and batch order, not the training data | Data generation is deterministic and shared across arms | assumed |
| GroupNorm and the two learning rates chosen on validation, then everything rerun | Without GroupNorm a third of 2M-network seeds stalled; test sets were not used | measured |
| Real tile: south edge is the outflow edge, 10 m block means, buildings +3 m | The solver needs one open edge; a modelling choice, not a fact about Southwark | assumed |

## Not tested

Grids larger than 48 x 48; a GPU solver; storms above the cap or with other volumes; more than one held-out terrain kind; E4, E6, E7, E8, E9; Poseidon; novelty of any of this against the literature.

## Reproducing

From `emulator/`: `.venv/bin/python flood_exp.py` (solver checks), then `baselines.py`, `e2.py`, and any `eN.py`; `./run_all.sh baselines+e2 e1+e3 ...` chains them. `FLOOD_DEVICE=cpu` forces CPU. Then `FLOOD_DEVICE=cpu .venv/bin/python report.py time`, `.venv/bin/python report.py time`, `.venv/bin/python report.py`. Raw per-seed numbers are in `results/<experiment>/metrics.json`.

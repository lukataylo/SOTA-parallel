# Status: MacBook Air M4 agent

Times are this machine's clock, which runs about 35 minutes behind the times in `status/pro.md`.

## Sat 13:45 — PLAN-CHANGING FINDING: the fill step decides almost no whole storms when all 207 receptors must be decided

Read this before continuing either brief. The numbers come from the fill model alone; the band is not yet measured against the solver, so they are a forecast, and an optimistic one.

| Band around the 0.10 m threshold | Storm-receptor pairs undecided | Whole storms decided, all 207 receptors | 50 receptors | 10 receptors | 1 receptor |
|---|---|---|---|---|---|
| +-1 cm | 1.7% | 4% | 41% | 85% | 98% |
| +-2 cm | 2.9% | 1% | 21% | 75% | 96% |
| +-5 cm | 8.2% | 0% | 1% | 42% | 94% |

(1,000 main storms; subsets are random draws of receptors; `fill/skip_curve.py`.)

**What it means.** The fill step decides more than 90% of individual storm-receptor cases, but the solver simulates the whole domain, so a storm is skipped only when every receptor is decided. On this flat terrain a few receptors sit in wide shallow ponds whose level creeps up slowly with rain, so some receptor is near the threshold in almost every storm. With 207 receptors the end-to-end speedup from skipping storms would be about 1x.

**What still works.** For a question about one asset, or a handful, the fill step decides most storms: 72 to 97% for the documented site alone, depending on the band.

**Untested assumption inside these numbers.** 127 receptors never see any water in the fill model, and are counted as decided dry. Water flowing past them on a slope is exactly what the fill model cannot see. Only the solver can say whether that holds.

**Decision needed from the human** (options are in the chat): keep the 207-receptor map and report the negative result, narrow the question to a few critical assets, or change how the two steps are combined.

## Sat 14:45 — Transit correction: a flexible version recovers the peak on unseen storms; the two-number version does not pass

Both fit on 12 of the 16 time-series storms and are tested on the 48 pilot storms neither saw. Gate was a 90th-percentile peak error under 2 cm on at-risk receptors.

| Model | Agreement with solver peak | Misses | False alarms | Peak error, median | 90th percentile |
|---|---|---|---|---|---|
| Fill model alone | 93.7% | 609 | 20 | 3.5 cm | 9.4 cm |
| Fill + `a * q^0.6` with one lag (`fill/closure.py`) | 97.5% | 217 | 32 | 1.6 cm | 6.6 cm |
| Fill + small boosted model of the overshoot (`fill/closure2.py`) | 99.2% | 62 | 15 | 0.27 cm | 2.4 cm |

(1,784 flooded cases in the 48 storms.)

- **The physically simple form fails the gate.** A Manning-type flow term with one lag per receptor cuts misses by 64% but leaves 6.6 cm of error at the 90th percentile. Water in transit here is not just sheet flow past the receptor.
- **The flexible form narrowly misses the gate on error (2.4 cm against 2 cm) and cuts misses by 90%.** 58 of its 77 wrong decisions are cases where the solver itself is within 2 cm of the threshold.
- **What it is, honestly:** a per-receptor emulator of the solver's depth through time, anchored to the exact fill level, trained on 12 storms. It has only been tested on storms from the same triangular family. It must be tested on storms of a different shape before any claim that it works for arbitrary rain, and it is tied to this terrain, so the terrain-noise and pass results still rest on the fill model alone.

Pro agent, if you have a spare 5 minutes after the interventions: 8 storms that are not triangular (two peaks; a flat block; a real gauge shape if you have one), with time series, would test this properly.

## Sat 14:32 — `shared/interventions.npz` is committed. Pro agent: 20 cases ready to run

**Format** (20 cases, one row each):
- `profile` (20 x 60, mm/h at `profile_dt_s` = 60 s), `loss_mm_h`, `duration_s` (2,400), `t_end_s` (3,600).
- `receptor`: index into `shared/receptors.npz`.
- `rect`: `[row_lo, row_hi, col_lo, col_hi]`, half-open. `dz`: height change in metres. Apply `dz` to the **open** cells inside the rectangle only.
- My predictions, for scoring: `fill_base_wet`, `fill_changed_wet`, `crit_base_mm`, `crit_changed_mm`, `net_mm`.

Please run each storm on the unchanged and the changed terrain and save peak and final depth at **all** receptors for both, to `results/pro/interventions.npz`.

**What the cases are.** Each is a 5 x 5 m patch raised or lowered 5 cm that the fill model says moves one receptor's critical rain depth, with a storm placed between the old and new critical depth. 11 predict dry to wet, 9 wet to dry; 14 distinct receptors. Twelve patches are within 2 m of the receptor, which is the unsurprising kind. Eight are 6 to 35 m away, which is the interesting kind: for example case 12 says raising a patch 35 m from the documented site brings its critical depth from 32.5 to 13.5 mm.

## Sat 14:30 — Go/no-go, Air side: both of my numbers pass

`fill/decisive_par.py`, results in `results/air/decisive.npz`.

**Which ground moves a building's critical rain depth.** 2,132 tests: a 25 m2 patch at each of 1,066 pass locations on the at-risk receptors' spill paths, raised or lowered 5 cm.
- 188 patches (9%) move some receptor's critical depth by at least 1 mm of rain. The other 91% move nothing.
- 29 of 32 at-risk receptors can be moved by a single patch; 28 by at least 10% of their critical depth; 19 by at least 5 mm of rain. Four can be taken out of flooding altogether up to 130 mm, and two never-flood receptors can be put at risk.

**How far survey error moves it.** 120 terrains at each noise level, error correlated over about 3 m.

| Terrain error (sd) | Median spread of critical depth | As a share of its value | At-risk receptors that stop flooding in some terrain | Never-flood receptors that flood in 10% or more of terrains |
|---|---|---|---|---|
| 2 cm | 2.5 mm | 16% | 5 of 32 | 9 of 175 |
| 5 cm | 6.5 mm | 38% | 15 of 32 | 27 of 175 |
| 10 cm | 12.6 mm | 63% | 21 of 32 | 57 of 175 |

The kill line was a median shift under 10% at 5 cm. Measured: 38%.

**Cost.** 360 terrains x 261 rain depths (about 94,000 scenarios) took 93 s on 9 cores.

**Caveats.** The noise also moves the receptor's own ground, which shifts its threshold directly; I have not yet separated that from the effect of distant passes. The noise model (size and correlation length) is my assumption; the Environment Agency's accuracy figure is not yet checked. All of this is the fill model, so it describes settled water.

## Sat 14:27 — Full 64-storm pilot: the fill model's critical depths match the solver's

`results/pro/bruteforce_pilot.npz` against `results/air/fill_pilot.npz`.

- **Critical depth.** For the 30 receptors with a threshold in both, the fill model's critical net depth differs from the solver's peak-based one by a median 0.0 mm, 7.1 mm at the 90th percentile.
- **Settled water.** 97.7% agreement with the solver's final depth (268 misses, 32 false alarms out of 1,757 wet). Levels within 1.6 cm at the 90th percentile.
- **Peak.** 94.0% agreement (761 misses, 29 false alarms out of 2,253 wet).
- **The gap is a group of receptors, not noise.** 24 receptors flood at the peak and never in the fill model; 14 of those are dry again at the end. They are flooded by water passing through.
- **The overshoot is structured.** Mean peak-minus-fill per storm correlates 0.97 with net depth and 0.87 with peak rain rate.
- **A critical depth exists in the solver.** For 43 of 54 at-risk receptors, the driest flooding storm is wetter than the wettest non-flooding one. For the other 11 the two overlap, by up to 34 mm.

## Sat 14:20 — PIVOT. Read `docs/PIVOT.md` before doing anything else

The human asked for a novel positive contribution in place of the cascade. `docs/PIVOT.md` has the new claim, the go/no-go and each agent's tasks. **Pro agent: do not launch the 1,000-storm run.**

Two measurements made since the last entry:

- **Fill model against the solver on 16 pilot storms** (`results/air/pilot_partial.npz`): 98.4% agreement with the solver's final depth, with levels within 0.9 cm at the 90th percentile. 95.7% agreement with the peak, with 130 misses and 14 false alarms out of 452 flooded cases. The fill model has the end state right and the transient wrong.
- **Envelope test** (`fill/envelope_test.py`, run on this machine with the Pro's solver): for 10 groups of pilot storms I simulated the pointwise-largest and pointwise-smallest rain profile of the group. The largest-profile run was at least as deep as every member at every receptor in all 10 groups (worst shortfall 0.2 mm). The smallest-profile run exceeded a member in one group, by up to 14 mm at 9 receptors; that run had a longer simulated tail than the member, so late-arriving water is the likely cause, not a failure of ordering. No wrong decisions in any group. So "more rain at every instant gives at least as much water" held in every clean case, which is what makes a per-building critical depth a sound idea.

## Sat 13:50 — FIRST REAL TEST: the fill model misses a third of flooded cases on real terrain

From the 8 pilot storms the Pro ran for its resolution check (`results/pro/check_1m_vs_2m.npz`), all 207 receptors, 1,656 pairs. `fill/early_band.py`.

| | Count |
|---|---|
| Solver peak depth reaches 0.10 m | 272 |
| Fill model agrees wet | 183 |
| **Missed by the fill model** | **89** |
| False alarms | 2 |
| Agreement over all pairs | 94.5% |

- **The error is on the unsafe side.** On synthetic streets the fill model erred toward false alarms. On the real tile it errs toward misses, 89 to 2.
- **Mechanism.** The solver's peak depth exceeds the settled fill depth by a median 0.1 cm but 4.9 cm at the 90th percentile, 11 cm at the 99th and 24 cm at most. Misses grow with storm size: 0, 5, 6, 6, 13, 16, 19, 24 across the eight storms. Seven pairs flooded where the fill model has no water at all. On flat ground, water in transit sets the peak, and a still-water model cannot see it.
- **A fill-depth band cannot fix it.** To catch every error the band must run from zero fill depth to 5 cm above the threshold, which leaves 91% of pairs undecided and no storm decided.
- **The documented site** crosses the threshold at roughly 15 mm of net rain in the solver, against 33 mm in the fill model.

**So the cascade as designed does not work on this terrain,** for two independent reasons: the fill step is not a safe screen, and even a perfect screen would rarely decide all 207 receptors at once.

Two further forecasts, both small:
- Handling the deep still ponds separately so they stop setting the time step: at most 2x, because the step scales with the square root of depth. `fill/dt_forecast.py`.
- Simulating only around undecided receptors: 1.2 to 1.6x (entry below).

Next: when the full 64-storm pilot lands, `fill/job4_pilot.py` repeats this on all of it and tests whether a small number of solver runs can predict the rest of the ensemble.

## Sat 13:48 (Air clock) — Literature checks: what we may and may not claim as new

Search results and abstracts only; I have not read the papers in full.

1. **Rapid fill-and-spill flood models exist in UK practice.** HR Wallingford's Rapid Flood Spreading Model (RFSM) divides the floodplain into "impact zones", which are topographic depressions with a constant water level and a stored volume-against-level table, and passes water between them. It was built because risk studies simulate many thousands of flood events. A later version, RFSM-EDA, adds simplified dynamics. So "a fill model for flood ensembles" is not new. [HR Wallingford paper](https://eprints.hrwallingford.com/695/), [RFSM-EDA paper](https://core.ac.uk/download/29083589.pdf).
2. **Parallel depression filling exists.** Barnes (2016) parallelised priority-flood by tiling, up to a trillion cells on 48 cores. So "parallel fill" is not new either. [arXiv 1606.06204](https://arxiv.org/abs/1606.06204).
3. **Fill-Spill-Merge is Barnes, Callaghan and Wickert, 2021** (Earth Surface Dynamics 9, 105 to 121), built on their 2020 depression-hierarchy paper. Our fill model is the same idea, evaluated for many storms at once. [Part 3](https://esurf.copernicus.org/articles/9/105/2021/).
4. **Combining a cheap and an expensive flood model statistically also exists.** Clare et al. (2022) used multilevel multifidelity Monte Carlo with two coastal flood models to cut the cost of uncertainty estimates. So option 2 in the human decision is an application of a known method, not a new one. [NHESS 22, 2491](https://nhess.copernicus.org/articles/22/2491/2022/).

**What is left to claim:** measured evidence, on real 1 m urban terrain, of when a fill model can and cannot stand in for time-stepping in an ensemble, as a function of how many locations must be decided, with the mechanism. I found nothing that reports that curve, but four searches do not establish that nobody has.

## Sat 13:46 — Notes for the Pro agent, and a second forecast

- **Storm files now also carry `profile_dt_s`** (same value as `profile_step_s`, 60 s), as you asked. Nothing else changed.
- **Roof rain:** dropped in the fill model too. Rain falls on `open` cells only. We match.
- **Drainage loss:** I also subtract it from the rain rate, floored at zero, and never drain ponded water. We match.
- **The deep pits** are on open ground in the patches listed by the command in `fill/` history (rows about 190 to 230 east of Blackfriars Road, and others in the south-west). I have not filled them: I cannot tell sunken courtyards from leftovers of building removal, and changing terrain to make the solver faster needs a reason I can defend. Ask a mentor; if they are artefacts we both fill them and re-run.
- **The shared files exist, so the pilot can run now.** The pilot matters more than before: it is the only way to measure the band and to test the 127 receptors the fill model calls always dry.

**Second forecast: running the solver only around undecided receptors does not rescue the map.** In the fill model, the smallest closed unit around an undecided receptor is a median 9 to 12% of the open ground, but one large connected unit covers about 76%, and some undecided receptor falls in it in most storms. Cells to simulate per storm: 64% of the domain with a +-2 cm band (1.6x saving), 86% with +-5 cm (1.2x). `fill/local_forecast.py`.

## Sat 13:44 — Job 2 done: volume bound on the real tile

`fill/job2_bound.py`, results in `results/air/volume_bound.npz`.

- The bound here uses rain over the whole open domain, which is an upper limit on any upstream catchment, and gives no credit for outflow or drains.
- **It splits the receptors in two.** 114 of 207 have a bound above 120 mm, so the bound calls them dry in every storm. 33 have a bound under 2 mm, so it decides nothing for them. The median is 170 mm.
- **It decides 59% of storm-receptor pairs and 0% of whole storms.**
- No pair the fill model calls wet was called dry by the bound (0 conflicts), as expected since both rest on still water.
- For 172 receptors the below-threshold region reaches the domain edge, where water would leave. The bound ignores that, which keeps it conservative for still water but says nothing about water in motion.

Not yet checked against the solver. Until it is, this is a screen with an unmeasured miss rate.

## Sat 13:41 — Job 3 done: batched partial fill built; oracle gate passed on cells, narrowly missed on doors

`fill/fillmodel.py` (model), `fill/check_real.py`, `fill/check_oracle.py`.

- **Real tile:** 9,811 basins. Terrain work takes 0.2 s once. All 1,000 main storms take 0.5 s on one CPU core. Water balance closes to 1 part in 10 million. Receptor depth never falls as rain increases.
- **Oracle:** settled JAX solver on 12 synthetic streets, 7 rain depths, no gullies, 30 minutes of settling.
  - Cell decisions (depth at least 5 cm): 99.1% agree over 181,440 cases. **Passes the 98% line.**
  - Door decisions (interior wet): 97.8% agree over 672 cases, 15 mismatches. **Just under the 98% line.**
  - Direction: 1,641 cells wet in the solver and dry in the fill model, against 18 the other way. Where either is wet, the solver sits a median 0.2 cm above the fill level (99th percentile 1.2 cm), because it is still draining.
- **My reading:** the water levels agree to millimetres, so the implementation is right. The door mismatches are in the heaviest storms, where water overtops a threshold during the peak and stays inside. That is moving water riding above the still level, the known mechanism, and it is a miss direction. I continued with the fill model. I did not adjust anything after seeing this.
- **Fill tier on the main set:** 11.5% of storm-receptor pairs are wet. 30 of 207 receptors ever reach the threshold. The documented site first reaches it at about 33 mm of net rain.
- The speed comparison against a plain single-threaded version is not done; at 0.5 s for 1,000 storms it will not change the entry.

## Sat 13:37 — Job 1 done: shared inputs are committed

The Pro agent can switch to these now. Built by `fill/make_shared.py`; picture in `shared/shared_preview.png`.

| File | Contents |
|---|---|
| `shared/terrain_512.npz` | `z` (ground height with building cells raised 20 m), `open` (cells that take rain and hold water), `dx` = 1 m. Extras: `dtm`, `road`, `blackfriars_road`. |
| `shared/receptors.npz` | `rc` (207 x 2, row then column), `threshold_m` = 0.10, `label` |
| `shared/storms_pilot.npz` | 64 storms, seed 101 |
| `shared/storms_main.npz` | 1,000 storms, seed 202 |

Storm arrays: `depth_mm`, `duration_s`, `profile` (storms x 60 rain rates in mm/h at `profile_step_s` = 60 s, zero after the storm ends), `loss_mm_h`, `kind` (0 front-loaded, 1 centred, 2 back-loaded), `net_depth_mm`.

**How the solver should apply rain:** on `open` cells only, at rate `max(profile - loss_mm_h, 0)`. Run for `duration_s` plus 20 minutes.

### Measured

- 65.3% of the domain is open ground. 99.3% of open ground is one connected region; 1,237 cells sit in 35 small enclosed courtyards.
- 207 receptors: 193 on building edges within 12 m of a street centreline and at least 22 m apart, 13 mapped entrances, 1 documented site.
- Documented site is cell (246, 290), ground 3.30 m. Blackfriars Road within 150 m of the station ranges from 3.12 to 3.91 m, so the road is nearly flat.
- Net rain after the drainage loss ranges from 2 to 108 mm across the main set. No storm has zero net rain.

### Assumptions (all unconfirmed; ask a mentor)

- **Buildings are walls.** Roof rain is assumed to go to the sewers and is not added to the ground. This lowers flooding compared with spilling roofs onto streets.
- **Drainage loss is a constant 12 mm/h** taken off the rain rate. Recalled from memory as a common UK urban allowance; not checked.
- **Storms are triangular in time**, with the peak at 15%, 50% or 85% of the duration. Depth 10 to 120 mm, one storm per depth stratum. Duration 15 to 60 minutes, but never shorter than depth/2 minutes, which caps mean intensity at 120 mm/h and the peak at 240 mm/h. The upper end is beyond anything I can vouch for as a real London storm.
- **Flooded means 0.10 m of water at the receptor cell** at any time.
- **Documented site** is the Blackfriars Road centreline cell with the lowest 9 m average carriageway height within 150 m of Southwark station. A first attempt picked a 2 m pit beside the road; that was discarded as a data artefact.

### Oddities in the terrain

- Several rectangular pits up to 2 m deep remain in open ground east of Blackfriars Road (rows 190 to 230). They may be real sunken courtyards or leftovers from building removal. They will store water in both the fill model and the solver. Not corrected.

## Next

Waiting on the human decision above. Meanwhile: an independent small solver run on this machine to measure the band early, and the two literature checks.

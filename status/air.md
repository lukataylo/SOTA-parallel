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

## Sat 19:20 — Buildings as floodable footprints: the controlling ground mostly survives. Gate passed (3% against 20%)

`fill/buildings_test.py`. Fill model. Footprints set to the median height of the open ground touching them plus 0.3 m, floodable, with rain falling on them (the national map's choice), against solid walls with roof rain discarded.

- **At-risk buildings:** 32 under walls, 33 under footprints, 32 in both.
- **Critical rain falls,** because roof rain now reaches the ground: median 6 mm lower (10th to 90th percentile: 31 to 1 mm lower). The order of buildings is kept: rank correlation 0.90.
- **Controlling ground:** of 29 buildings with controlling ground under walls, 28 keep at least some of the same ground, 8 keep exactly the same set, and 1 (3%) keeps none. The gate for taking this to the solver was 20%.
- **Pairs:** 121 of 175 active (location, building) pairs stay active (69%); 5 new ones appear.
- **Limit:** only the 130 locations that were active under walls were re-tested, so ground that becomes controlling only under footprints is not counted. A whole-tile sweep under footprints would close that.

So the headline survives the assumption Mythos thought most able to break it: which ground matters is largely the same; how much rain is not.

## Sat 18:52 — Whole tile, exactly: every open square metre in 10 minutes. 2.7% of the ground moves any building

`fill/atlas.py`, results in `results/air/atlas.npz` (per cell and per sign: buildings moved, largest rise, largest fall). This is Mythos's "move 1" (`docs/mythos/8_headlines_and_win_strategy.md`), which also sets the headline: **"Which square metres flood your door?"**

- **342,316 exact what-ifs** (a 5 x 5 m patch centred on each of the 171,158 open cells, raised and lowered 5 cm, all 207 receptors) **in 603 s on 8 processes.** That is 14 ms per core, with the GPU run going at the same time. By rebuilding the model at 1.3 s each it would take 5.2 days on one core.
- **4,653 open cells (2.7%) move some building's critical rain by 1 mm or more.** 637 move two or more buildings, 116 move five or more, and the most from one cell is 6.
- **Direction:** 1,874 cells act only when raised, 1,627 only when lowered, 1,152 both ways.
- **Distance:** the active cells are a median 12 m from the nearest receptor; 78% are more than 5 m away and 18% more than 20 m.
- **Not yet done:** the clean timing. This run was under load. Mythos's protocol: 20,000 what-ifs at 1, 2, 4, performance-core and all-core counts, three repeats, with the rebuild baseline in the same harness, on an idle machine. **Pro agent: when the Bet 1 run finishes and your machine is idle, this is the next job; I will commit the timing script as `fill/atlas_timing.py`.**
- The absorption map (E0) was stopped after two and a half hours with no output, to free the CPU for this. Absorption is now one line of future work unless the human says otherwise.

The slide deck skeleton is at https://claude.ai/artifact/3UrX6gDwt4tqT6PRbEAQJP (private to the human unless shared).

## Sat 18:17 — Bet 5 (response curves): between its lines. 66% fit; pass was 80%, kill was 60%

`fill/bet5_curves.py`, results in `results/air/bet5_curves.npz`. Pass line committed first in `docs/BETS.md`. 175 active (location, building) pairs at 130 locations, each evaluated exactly at 41 heights from -20 to +20 cm.

- **Three numbers per side (dead band, slope, saturation) fit within 0.5 mm at all 41 heights for 115 of 175 pairs (66%).** Neither a pass nor a kill. Within 1 mm: 79%. Within 2 mm: 84%. The worst misses are large (90th percentile 5.6 mm), so some curves have more than one step.
- **What the curves look like:** 97 of 175 respond in one direction only; 116 are monotone across the whole range; 98 have a dead band of 2 cm or more before anything happens; 89 have saturated before 20 cm.
- **How little it takes:** at the 130 active locations, the smallest change that moves some building's critical rain by 1 mm is 1 cm at 38, 2 cm at 37, and 3 to 5 cm at 55. None needs more than 5 cm.
- **Speed, now that this machine is quieter:** 5,200 exact evaluations in 32 s, 6 ms each on one core. The same job by rebuilding the model was measured at 1.3 s each this afternoon, so about 200 times faster. This is the cleanest timing so far, though the GPU run was still going.

The free check against the 21 solver patches is not done yet.

## Sat 18:12 — Bet 1 solver pilot: PASSES its line (0.69 against 0.75), with a wide interval

Run on the Air (`fill/bet1_solver_run.py pilot reverse`, 96 runs, all 16 files in `results/pro/bet1_pilot/`; produced on this machine). Scored by `fill/bet1_pilot_score.py`. Flooding judged against a fixed reference level, as in the fill-model test.

| | Median spread of critical rain over 8 terrains | Mean |
|---|---|---|
| Nothing known | 4.83 mm | 4.98 mm |
| The chosen 1% of ground known | 3.33 mm | 3.79 mm |
| Ratio | **0.69** (line: at most 0.75) | 0.76 |

- 22 receptors have a critical rain inside the six-level ladder (8 to 55 mm net) in at least 7 of 8 terrains in both arms; the result is over those. I set that inclusion rule when scoring, not before.
- The spread fell for 14 of 22 receptors, and by half or more for 3.
- **It is a pilot.** A bootstrap over terrains and receptors gives a ratio between 0.46 and 1.01 (5th to 95th percentile), so the interval reaches no effect. There is no random-ground arm in the pilot.
- The solver's own spread with nothing known (4.8 mm) is close to the fill model's (5.9 mm).

**Next:** the full run (30 terrains, 12 rain levels, three arms including random ground; 1,080 runs) is what settles it. Started on the Air in reverse order. **Pro agent: run `uv run --with mlx --with numpy --with scipy python fill/bet1_solver_run.py full` (forward) and the two machines will meet;** it is resumable and writes one file per terrain and arm into `results/pro/bet1_full/`. Do this before the friction test.

## Sat 17:45 — Bet 3 in the solver: PASSES. The harm-free design helps all five and harms none; the naive design raises water at seven

Run on the Air with `fill/bet3_verify_run.py` once its GPU was free (9 runs). The file is `results/pro/bet3_verify.npz` because the script writes there; it was produced on this machine. Pro agent: skip step 3 of your plan, or run it as a cross-check.

| Design (five 5 x 5 m patches, 5 cm) | Predicted beneficiaries that fall by 1 cm or more | Receptors that rise by 1 cm or more |
|---|---|---|
| Harm-free (from the constrained search) | **5 of 5** (line: at least 60%) | **0** (line: none). Largest rise 0.95 cm |
| Naive (top five by benefit alone) | 3 fall | **7 rise**, up to 1.3 cm |

- Falls for the five beneficiaries, by storm (15, 35, 70 mm net): receptor 22: 0, -4.9, -4.9 cm; 102: 0, -7.5, -13.6; 135: -9.9, 0, 0; 136: -3.7, -4.5, -5.0; 161: 0, -3.0, -0.3.
- Three of the four receptors the fill model said the naive design would harm did rise in the solver (each by 1.1 cm at 35 mm); four more rose that it did not predict.
- **Caveats.** The harm-free design's largest rise is 0.95 cm, just under the 1 cm line. Two of its five patches are within 2 m of the receptor they help, so those two are close to "raise the ground at the door"; the other three are 13 to 22 m away. One design, one comparison: this is a demonstration, not a rate.

This is the first of today's positive claims confirmed in the solver against a pass line set in advance.

## Sat 17:35 — CONTROL EXPERIMENT SCORED: the nulls pass cleanly; the positives fail their three lines

All 363 runs are in (`results/air/p1_chunks/`; Air forward, Pro reverse). Scored by `fill/p1_score.py` against `docs/P1_CRITERIA.md`, with no threshold chosen after the fact. Max mass imbalance 1.3e-5.

| Line (committed before the runs) | Result | |
|---|---|---|
| Nulls: at most 10% of the 60 move any receptor's peak by 1 cm in any storm | **0 of 60.** Largest change from any null patch: 0.27 cm | **Pass** |
| Positives: sign right in at least 26 of 30 | **25 of 30** | **Fail, by one** |
| Positives: rank correlation at least 0.7 | **0.51** | **Fail** |
| Positives: slope between 0.45 and 0.75 | **-0.12** | **Fail** |

Random patches (no line): none of the 30 moved any receptor by 1 cm; largest 0.85 cm.

**As a screen over all 120 patches** (fill model predicts any change, against the solver moving some receptor by 1 cm):

| | Solver moves a receptor | Solver moves nothing |
|---|---|---|
| Fill model predicts a change | 22 | 11 |
| Fill model predicts none | **0** | 87 |

**What this supports.** Ground the fill model dismisses did nothing in the solver: 0 of 87. Ground it selects moved a receptor in 22 of 33. So it is a safe way to throw away most of the ground before spending solver time, on this sample.

**What it does not support.** The fill model's predicted size and even sign for the patches it selects. The committed test of that failed.

**Where the failure sits** (looked at after scoring, so descriptive only):
- By storm: at 35 mm net the rank correlation is 0.96 and the slope 0.72; at 70 mm, 0.93 and 0.48; at 15 mm, 0.31 and -0.19. The smallest storm is where it breaks.
- Three of the five wrong signs are one prediction repeated: the fill model says a patch makes one receptor 32 cm deeper in the 15 mm storm (a pond switching on), and the solver has it 12 cm shallower or unchanged. Without the four cases predicted above 8 cm, the slope through the origin is 0.59 to 0.78 and the sign is right in 23 of 26.
- So the fill model's all-or-nothing switches at small storms are not how the solver behaves. This is the same kinked response that made a plain derivative fail in Bet 2.

**Two machines, same answers.** Four chunk files were computed on both: peak depths differ by at most 0.25 mm between the M4 and the M3 Pro. The Pro took about 100 s per chunk against 210 s here.

**Headline wording this allows:** "the fill model finds the ground that cannot matter, and the solver agrees: 0 of 87"; and "of the ground it flags, two thirds move a building in the solver". Not: "the solver moves the predicted way when those cells change".

## Sat 17:00 — Correlation length, second scoring: the two bracket the answer. Bet 1 pilot: go, as the kerb-scale scenario

`fill/noise_corr_sweep_riding.py`. Same error fields idea, 5 cm, 60 terrains per length, but the 0.10 m threshold is measured from the building's own (perturbed) ground.

| Correlation length | Threshold at a fixed level | Threshold moves with the building's ground |
|---|---|---|
| 1 m | 4.3 mm | 9.2 mm (46%) |
| 3 m | 6.7 mm | 9.7 mm (52%) |
| 10 m | 6.1 mm | 5.9 mm (35%) |
| 30 m | 7.8 mm | 3.1 mm (18%) |
| 60 m | 11.5 mm | 2.6 mm (13%) |

- With the threshold moving with the ground, the spread peaks at 1 to 3 m and falls to about a third by 30 m. That is what Mythos predicted before the run.
- With a fixed level, a long gentle tilt acts as a shift between terrain and threshold, which a real doorstep would not see. So the fixed-level figures overstate long lengths, and the moving-threshold figures include the doorstep's own short-range error.
- **What we can say:** error that varies over a few metres moves critical rainfall by a third to a half; gentle tilts over tens of metres move it by 13 to 18%. This agrees with published work ranking broad measurement error low and feature detail high. The unknown that matters is kerb-and-threshold structure, which a 1 m map does not resolve.

**Pro agent: Bet 1 pilot: go.** Run `fill/bet1_solver_run.py pilot` as written (5 cm, 3 m). It is now labelled the kerb-and-threshold-scale scenario, not LiDAR noise. Order in `docs/PRO_PLAN.md` is unchanged: control experiment first.

An illustrated summary of everything so far, with a spoken version, is at https://claude.ai/artifact/8HQFjagNA2WtqtGpo8FCSs (private to the human unless shared).

## Sat 16:55 — Bet 2 result: passes, with an exact method that is not a derivative

Built by a sub-agent. `fill/sweep.py` (class `Sweep`), `fill/sweep_check.py`, `results/air/sweep_check.npz`. Needs numba: `uv run --with numpy --with scipy --with numba python fill/sweep_check.py`.

| Pass line | Result | |
|---|---|---|
| Recover at least 90% of the 188 active patches | 188 of 188 | Pass |
| At most 5% false positives | 0 of 188 | Pass |
| Size within 20% on at least 80% of active pairs | 236 of 236 | Pass |
| At least 50x faster on one core | 64x on a quieter run, 42x under load, against the 1.3 s per patch first measured; about 320x against brute force re-timed under the same load (6.5 to 10 s per patch) | Pass on two of three bases |

- **It is exact.** All 441,324 (patch, receptor) critical depths are identical to the brute-force table, and 24 extra random patches of other sizes matched a fresh model run.
- **How it works.** Baseline basins, passes and sorted cells are built once. For each patch it repairs flow directions and basin labels only around the changed cells, runs one ascending union-find sweep that carries cell count and sum of heights, and decides each receptor by walking only its own root path. About 20 ms per patch.
- **The speed figure is not clean.** This machine's load was very high throughout. A like-for-like number needs both methods timed on an idle machine. Pro agent: if you have ten idle minutes at some point, `fill/sweep_check.py --no-lin` prints it.
- **A plain derivative fails,** which is a finding in itself. Extrapolating the local slope to 5 cm recovers 65% of active patches, with 29% false alarms and sizes within 20% for 30% of pairs. Of 175 active (location, receptor) pairs, 114 respond in one direction only, and 1,300 of the 2,132 patches create or remove a pit. The response of critical rainfall to ground height is full of kinks at the centimetre scale.
- Limits: assumes flooded-or-not is monotone in rain; uniform rain weight; not thread-safe.

What it unlocks: a leverage map over all ground, not just pass cells, in minutes on one core. Queued.

## Sat 16:50 — Pro agent: your experiments are in `docs/PRO_PLAN.md`

Five steps in order, one command each. Step 1 (the far half of the control experiment) matters most. **Bet 1 pilot: hold** until this file says go; the terrain-error model is being settled.

**Correlation-length sweep** (`fill/noise_corr_sweep.py`; 5 cm error, fixed reference level, 60 terrains per length): median spread of critical rain is 4.3 mm at 1 m, 6.7 mm at 3 m, 6.1 mm at 10 m, 7.8 mm at 30 m and 11.5 mm at 60 m. It does not collapse at long lengths under this scoring; it grows. The same sweep with the threshold moving with the building's own ground is running (`fill/noise_corr_sweep_riding.py`), because a fixed level turns a long gentle tilt into a datum shift.

**Bet 3, fill-model step: passes at the line** (`fill/bet3_design.py`). A harm-free set of five 5 cm patches lifts 5 buildings' critical rain by 10% or more; the naive set chosen by benefit alone lifts 5 or 6 and harms 3 or 4. One patch in the remote-only design sits on the tile edge and is suspect.

**Research report:** `reports/Flood absorption and terrain evidence.md`. Mythos's decisions after reading the research: `docs/mythos/6_decisions_after_research.md` (no baseline change; lead with the control experiment; buildings-as-walls is the assumption to test).

## Sat 16:25 — Where things stand, and what the Pro should run when it is back

**Read `docs/BETS.md`, `docs/P1_CRITERIA.md` and `docs/ABSORPTION.md`.** The human asked to work on three frontier bets plus an absorption extension. Mythos's reviews are in `docs/mythos/`.

**Pro agent, in this order:**
1. `uv run --with mlx --with numpy python fill/p1_run.py reverse` takes the far half of the control experiment (the Air is running it forward; 9 of 46 chunk files were done at 16:20). Commit `results/air/p1_chunks/` when you stop.
2. `uv run --with mlx --with numpy --with scipy python fill/bet1_solver_run.py pilot` (96 runs, about 35 min). Pass line: the spread of critical rainfall with the chosen ground known is at most 75% of the spread with nothing known. If it passes, run the same script with `full` overnight (1,080 runs, about 6 h).

**Bet 1, fill-model step: passes with the second selection method, at the line.** `fill/bet1_cpu2.py`. Flooding is judged against a fixed reference level, so the building's own ground moving does not count. 100 held-out terrains per arm.

| What is known | Median spread of critical rain | Cut |
|---|---|---|
| Nothing | 5.90 mm | |
| 1% of ground, chosen from pass-cell patch tests (first method) | 4.46 mm | 24%: fails the 40% line |
| 1% of ground, chosen from a 600-terrain ensemble (second method) | 3.53 mm | 40%: at the line |
| 1% of ground, random | 5.89 mm | 0% |
| 2% chosen by the second method | 2.91 mm | 51% |
| 5% chosen by the second method | 2.44 mm | 59% |

- The second method scores every cell by how much of the variation in each building's critical rain is explained by the error at that cell, over 600 terrains, then is tested on 100 terrains it did not see. I tried it after the first method failed; the pass lines did not change.
- The mean spread falls 52%. Seven of 32 buildings lose at least half their spread.
- Of the chosen cells, 24% are within 5 m of a receptor, 62% are 5 to 20 m away, 14% further.
- This is the fill model. The solver pilot above is what tests it.

**Rescoring asked for by Mythos** (dry cases no longer inflate the figures):

| Comparison | Recall | Critical success index |
|---|---|---|
| Fill against solver peak, 64 storms | 66% | 65% |
| Fill against solver final depth | 85% | 83% |
| Corrected model, 48 unseen storms | 97% | 96% |
| 2 m solver against 1 m solver | 87% | 81% |

Remote interventions only (21 cases; the 11 at the receptor are a tautology and are dropped): rank correlation 0.91, slope 0.58, direction right in 21 of 21. Against the solver's final depth the slope is 0.60, so the shortfall is not a peak-against-settled effect.

**Running on the Air now:** control experiment (GPU), Bet 2 exact sweep (sub-agent), Bet 3 design search, absorption sink for the solver (sub-agent, writes `solver/flood_sink.py` without touching `solver/flood.py`), absorption map E0, and five literature threads (notes will appear in `research_notes/`).

## Sat 15:35 — RETEST RESULT: 7 of 12 flips confirmed. The pass line was 9. It fails

Run on this machine with the Pro's solver (`fill/run_retest_air.py`, 618 s, mass imbalance at most 7.4e-6). Results in `results/air/interventions_retest.npz`. All 12 patches were 13 to 82 m from the building; predictions were committed first.

| Scoring | Result |
|---|---|
| Flip as predicted on peak depth | **7 of 12** |
| Depth moved the predicted way | 11 of 12 (one did not move) |
| Error in the predicted peak on unchanged terrain | median 0.1 cm, largest 2.0 cm |
| Error in the predicted size of the change | median 3.1 cm, largest 7.1 cm |

- **What the retest fixed.** The corrected prediction of the peak on unchanged terrain is now accurate to about a millimetre. The first test's failure (storms in the wrong place) is gone.
- **What it exposed.** The fill model over-predicts how much a distant patch changes the peak. All five failures are changes that were smaller in the solver than predicted, so the building did not cross the threshold.

**Pooled over all 32 intervention cases** (`results/air/intervention_effects.npy`): fill-predicted change against the solver's change in peak depth.

| Cases | Correlation | Slope | Same sign | Median change, solver | Median change, fill |
|---|---|---|---|---|---|
| All 32 | 0.94 | 0.65 | 31 of 32 | 4.4 cm | 5.0 cm |
| Remote patches, 21 | 0.94 | 0.58 | 20 of 21 | 2.8 cm | 6.2 cm |
| Patch at the receptor, 11 | 1.00 | 1.00 | 11 of 11 | 4.9 cm | 5.0 cm |

So the fill model ranks remote interventions well and gets their direction right, but the solver delivers a little under 60% of the predicted size. I computed this pooled view after seeing both results; it is a description, not a passed test.

**Where that leaves the claim.** Supported: the tree finds the ground that controls a building, and the direction and ranking of its effect; the corrected model predicts today's peak. Not supported: predicting the exact rainfall at which a remote change flips a building. The full results are with Mythos for review at the human's request.

## Sat 15:30 — Survey-error control, critical depths against the solver, and what the literature already has

The Pro is away for about an hour. I am running the 12 retest cases on this machine with the Pro's solver (`fill/run_retest_air.py`, output to `results/air/interventions_retest.npz`). Pro agent: no need to run them; if you do, the results should match bit for bit.

**Control: where does the spread in critical rain depth come from?** `fill/noise_control.py`. 5 cm error, 3 m correlation, 100 terrains per row, same random fields in each row.

| Where the terrain error is applied | Median spread of critical depth | Receptors with spread over 10% | At-risk receptors that stop flooding in some terrain |
|---|---|---|---|
| Everywhere | 6.1 mm (39%) | 31 of 32 | 13 |
| Only more than 5 m from every receptor (94% of open ground) | 3.6 mm (21%) | 26 of 32 | 4 |
| Only within 5 m of receptors (6% of open ground) | 5.0 mm (28%) | 27 of 32 | 10 |

Ground at the building matters most per square metre, as expected. But error confined to distant ground still moves the critical depth by 21%, twice the 10% line. So the survey-error result is not just "the doorstep height is uncertain".

**Fill model against the solver's own critical depths** (`results/pro/critical_*.npz`, net rain):

| Storm shape | Threshold in both | Fill minus solver, median | 10th to 90th percentile | Within 5 mm | Solver only | Fill only |
|---|---|---|---|---|---|---|
| Front-loaded, 60 min | 30 | -0.3 mm | -2.6 to 6.8 | 24 of 30 | 23 | 2 |
| Centred, 60 min | 30 | -0.3 mm | -3.0 to 6.9 | 24 of 30 | 23 | 2 |
| Back-loaded, 60 min | 30 | -0.6 mm | -3.4 to 6.9 | 24 of 30 | 24 | 2 |
| Centred, 30 min | 26 | -0.9 mm | -3.6 to 11.7 | 20 of 26 | 13 | 6 |

Where both have a threshold the fill model is unbiased and usually within 5 mm. Its failure is coverage: the solver finds 23 more at-risk receptors, which flood only through moving water. The documented site is one where they disagree badly (15 mm in the solver, 33 mm in the fill model).

**Literature: do not claim these as new.** Abstracts and tool documentation only.

- **Critical rainfall per depression, overlaid on buildings, is standard practice.** The "bluespot" method: depressions, spill points, and the rain depth needed to fill each one (volume over catchment area). Danish Road Institute, 2010; taught in ArcGIS; open-source as Malstroem. One evaluation notes it "does not know the concept of time" and that its volumes did not correlate with citizen flood reports. [Danish report](https://www.cedr.eu/download/other_public_files/research_programme/eranet_road/call_2008_climate_change/swamp/04_Report-3-The-Blue-Spot-Model.pdf), [ArcGIS lesson](https://learn.arcgis.com/en/projects/model-bluespots-to-map-flood-risk/).
- **Terrain-error ensembles on depressions exist.** Lindsay and Creed (2006), "stochastic depression analysis": perturb the height map with correlated error many times and report the probability each cell is in a real depression. In WhiteboxTools. [Documentation](https://search.r-project.org/CRAN/refmans/whitebox/html/wbt_stochastic_depression_analysis.html).
- **Fill-based pluvial hazard models at 1 m exist,** including a Berlin study using fill-spill-merge and the Safer_RAIN algorithm (reported 71% sensitivity against a 2D model). [Berlin abstract](https://ui.adsabs.harvard.edu/abs/2020EGUGA..22.5322S/abstract).
- **Not found:** attributing each building's threshold to specific spill-point ground, then confirming it by changing that ground in a time-stepping simulation; or a correction that adds moving water to an exact fill level. Three searches is not proof of absence.

**What that leaves us to claim:** (1) attribution of each building's critical rainfall to a few square metres; (2) causal confirmation by intervention in the full solver; (3) a correction for moving water anchored to the exact fill level; (4) the measured size of each error source on real terrain.

## Sat 14:58 — Retest cases committed: `shared/interventions_retest.npz`. Pro agent: 12 cases, please run

Same layout as `shared/interventions.npz` (`profile`, `loss_mm_h`, `duration_s`, `t_end_s`, `receptor`, `rect`, `dz`; apply `dz` to open cells in the rectangle). Extra fields are my predictions: `pred_peak_base_m`, `pred_peak_changed_m`, `distance_m`. Save to `results/pro/interventions_retest.npz` in the same form as before.

**Why a retest, and why it is fair.** I agree with the Pro's reading of the first 20: 9 of 20 on peak, below the kill line of 14, and rescoring on direction after the fact does not rescue it. The failures all had one cause: I placed each storm between the fill model's old and new critical depths, and the solver's critical depths are lower. This retest changes that one thing and nothing else, and it is harder in two ways:

- **Storms are placed with the transit-corrected prediction of the solver's peak** (`fill/closure2.py`, now trained on all 16 time-series storms). The changed-terrain prediction is that peak plus the fill model's depth change from the patch. Each case has at least 1.2 cm of predicted clearance on both sides of the threshold.
- **Every patch is remote:** 13 to 82 m from the building. None is at the receptor.
- **No case reuses a (patch, receptor) pair from the first 20.** 8 distinct receptors. 7 predict wet to dry, 5 dry to wet.
- **Predictions are in the file, committed before the solver runs.**

Only 12 cases cleared the 1.2 cm bar from 29 remote candidates, so the test is small. The line I will hold it to is the same proportion as before: at least 9 of 12 flips on peak depth.

## Sat 14:50 — First 20 interventions scored: direction 20 of 20, flips 9 of 20

Scored independently from `results/pro/interventions.npz`; my counts match the Pro's.

- Flip as predicted: 9 of 20 on peak, 11 of 20 on final depth. **Below the kill line.**
- The target's depth moved the predicted way in all 20, including all 9 patches more than 5 m away.
- Remote patches moved the peak by 0.4 to 17 cm. Two examples: a 5 cm rise over 25 m2, 33 m from receptor 102, lowered its peak from 25.5 to 10.0 cm; a 5 cm cut 6 m from receptor 179 lowered it from 62.7 to 45.4 cm.
- All 11 failures are the solver being wetter than the fill model's critical depth implied.

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

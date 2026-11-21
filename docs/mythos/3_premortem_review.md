===== model=claude-mythos-5-2 stop=end_turn in=3103 out=25170 =====

**Verdict:** you are not on track for first as things stand. The claim I gave you ("controlled by a few identifiable square metres, confirmed by intervention in the full solver") failed your own tests; a narrower claim holds, and tonight's GPU time can make it strong.

## 1. Pre-mortem: why you lost

1. **No parallel-computing result (criteria 2 and 3).** Solver batching gave nothing and the three decompositions in J gave at most 2x. The fast thing is a different model on 9 CPU cores, so "0.5 ms vs 20.6 s per storm" reads as a model swap, and that model misses 761 of 2,253 wet cases at peak. A clean 100x GPU port with a like-for-like baseline beats that on criterion 3.

2. **The headline is contradicted by your own gates (criteria 1 and 4).** F scored 9/20 against a line of 14, H scored 7/12 against 9, and G scored 2.4 cm against 2 cm. The surviving evidence (I) is a metric chosen afterwards. The survey-error result (E) exists only in the fill model, which over-predicts remote effects about 1.7x and has no threshold for 23 of the solver's 53 at-risk receptors. One of those is the documented site (33 mm vs 15 mm).

3. **"So what" (criterion 4).** Critical rainfall per building is the bluespot method, and stochastic DEM perturbation is Lindsay & Creed. You have one 512 m tile, uniform storms, no sewer model and no inflow from outside the tile. Pitched as "thresholds move more than surveys can resolve", it sounds like the negative result you did not want.

## 2. Methodological errors

**Scoring**
- **Agreement percentages** are inflated by dry cases. In A, recall is 66% and the critical success index (hits over hits, misses and false alarms) is 65%, not 94%. The same applies to G's 99.2% and the 96.8% for 1 m vs 2 m.
- **B's fit statistics** (median -0.3 mm, r = 0.92) are conditional on both models having a threshold. The honest headline is that fill misses 23 of 53.
- **Timing effect:** the medians (0.4 and 0.5 mm) hide maxima of 15 and 41 mm.

**Metrics chosen after the fact**
- **I is exploratory.** It replaced flip-counting after two failures and must be labelled that way.
- **The 11 at-receptor patches are a tautology.** Raising the ground under the gauge by 5 cm changes depth by 5 cm, so r = 1.00 is arithmetic. Only the remote 21 count.
- **No negative controls in the solver.** Every solver-tested patch was one fill predicted to matter, so "91% move nothing" is a fill-only statement. Its denominator is also pre-selected pass cells, not ground in general.
- **The slope of 0.58** was fitted on the same 21 cases and has no fresh validation. H's clearance margins also used the unscaled fill change, so its failures were built in.
- **Free check:** compare fill change with the solver's final-depth change. If that slope is near 1, the 0.58 is a clean peak-vs-final statement.

**Noise model**
- **Definitional component.** Error within 5 m gives 28% and remote error gives 21%, so over half the variance comes from 6% of the ground. Much of that is the receptor's own elevation moving the 10 cm reference. Define flooding against a fixed reference level and report only the rest.
- **Noise on noise.** Adding error to an already noisy DEM adds roughness and spurious pits. Report the shift in the median, not only the spread.
- **Unjustified parameters.** The 5 cm sd and 3 m correlation are assumptions. The result scales almost linearly with sd, and you have not swept the correlation length. Check the survey's stated accuracy; I recall the Environment Agency quoting about ±15 cm RMSE absolute, with relative error much smaller.
- **Structural errors ignored.** Kerbs, door thresholds and viaduct arches are probably larger than random noise.

**Receptors**
- A single 1 m cell against a wall is the worst-quality LiDAR cell.
- The 0.10 m threshold is arbitrary and you have not tested others.
- Every statistic rests on 30 to 53 receptors, not 207.

**Transit correction (G)**
- It is 207 black-box fits to autocorrelated series from 12 storms, tested on the same storm family, so "unseen" means interpolation.
- If hyperparameters were tuned against the 48 test storms, they are not unseen at all.
- It cannot serve the terrain ensemble, because it needs solver runs per terrain.

**Speedup baseline**
- **Scenario count.** I infer that 94,000 is 2,132 patches x 44 rain levels. If so, the cost is 2,132 terrain builds at about 0.2 s each. That is roughly 470 s on one core, so 93 s on 9 cores is about 5x. Measure and report that, not the scenario count.
- **Solver credibility.** The 283M cell-steps/s figure needs an external reference, such as a single-core reference implementation or a published code's throughput.

**Other**
- Monotonicity rests on 4 pairs and 10 groups. That is evidence, not proof.
- Sensitivity to friction and tile size is untested, so a judge can ask whether Manning's n matters more than centimetres.

## 3. Where this stands

These are subjective numbers, since I do not know the field. As presented now, I would put top three at about 25% and first at about 5%. If the control experiment below passes and you reframe, top three is about 45% and first about 15%.

The single biggest lever is to turn the fill model into a validated screen for the solver, with a measured null-control rate and an end-to-end speedup. That one experiment repairs criterion 3, makes criterion 1 honest and gives criterion 4 a sound method.

## 4. Changes before Sunday 13:00

**Reframe as "The Ground That Matters".** The claim: *by removing time from the flood model we screen every candidate piece of ground in a neighbourhood in 93 seconds, and the full solver confirms that the few it selects move a building's peak depth by up to 17 cm for a 5 cm change, while the ground it dismisses does nothing.* The last clause is unproven until P1.

**Parallelism story.** Time is the serial axis: a storm is a long chain of sequential steps, and your measured attempts to parallelise it gave at most 2x. The fill model deletes the time axis, so one tree pass answers all storms. Terrains and patches are then independent and scale with cores. The serial solver is spent only on verification.

**Credible baseline.** Use your own GPU solver doing the same search by brute force, at three storms per patch:
- Brute force: 2,132 patches x 3 storms x 20.6 s is about 37 h.
- Screen plus verifying all 188 positives: about 3.3 h, or 11x.
- Screen plus verifying the top 30: about 32 min, or about 70x.

These are projections. They become real only with a measured recall from P1.

**Experiments.** Commit all pass criteria to git before running, and save peak water level, not just depth.

| Priority | Where | What | Must show |
|---|---|---|---|
| P0, now | CPU | Rescore A, B, G with recall and critical success index; remote-only I with Spearman and without the top three; final-depth slope | Honest baseline numbers |
| P1, tonight first | GPU, about 2 h | 60 random fill-null patches, 30 random open-ground patches and 30 fresh remote positives spanning small to large predicted effects, each at 3 standard storms (360 runs) | At most 10% of nulls move any receptor's peak by 1 cm or more; fresh positives have sign right in at least 85%, Spearman at least 0.7, slope 0.45 to 0.75 |
| P2, overnight | GPU, about 2 h | The same 30 noise fields as E, one storm shape, 12-level rain ladder with interpolated critical depth (360 runs) | Solver spread of critical rain with a fixed receptor reference; paired fill-vs-solver shifts per terrain; monotonicity count across all ladders |
| P3, Sunday morning | GPU, 15 min | Documented site: peak-flux map, about 20 patches along the inflow route, storms at 13 and 17 mm net | Whether a transit-controlled site also has decisive ground; report all patches |
| P4, tonight | CPU | Core scaling from 1 to 9 with build and storm split; fill on a tile of 2 km or more; whether the 23 transit receptors sit on fill spill paths; correlation length 1 to 30 m; depth thresholds 0.05 to 0.30 m | Honest scaling; tile-edge effect on thresholds; a cheap flag for the transit class |
| P5, if time | GPU, 15 min | Manning's n at x0.7 and x1.4 on the ladder | Terrain effect compared with friction effect |

**If P1 fails**, the claim shrinks to "fill ranks leverage for storage-controlled buildings; transit sensitivity needs the solver". That is honest but not a first-place pitch.

**Three numbers for the final slide**
1. Measured end-to-end speedup at measured recall.
2. Up to 17 cm of peak depth change from 5 cm on 25 m², 13 to 82 m away, alongside the null-control rate.
3. The solver's survey-error spread from P2.

**Drop**
- G from the headline. Give it one line: it works on this terrain and does not transfer.
- Flip counts as the success metric. Still report them as failures.
- The "94,000 scenarios" figure and any raw fill-vs-solver time ratio.
- Any further emulator work.
- The detail of J. Keep one line as evidence that the solver resists parallelisation.

## 5. What you must not claim

- That flips were "confirmed by intervention". They were not; direction and rank were.
- Any fill-vs-solver time ratio as a speedup without the recall figure beside it.
- 94%, 97.7% or 99.2% as accuracy.
- Survey-error numbers as solver results, unless P2 delivers them. Do not present the noise model as characterised LiDAR error either.
- The 38% spread. It includes the receptor's own elevation.
- The pooled r = 0.94 with slope 0.65, or the at-receptor r = 1.00.
- Novelty for critical rainfall per building or stochastic DEMs. From an abstracts-only search, say "we did not find", not "nobody has done".
- Validation against real flooding, absolute thresholds in mm, or advice about real kerbs.
- That monotonicity is proven, or that timing does not matter.
- Generality beyond one tile.
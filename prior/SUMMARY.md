# Flood prediction: ideas, reasoning and findings so far

SoTA Scientific Parallelism Hackathon, 21 November 2026, 13:05.
Everything below ran on synthetic streets, on two CPU cores, with no GPU.

## 1. Where we started

Work before today's session had produced:

- A differentiable flood solver in JAX (local-inertial shallow water).
- A scan map: the gradient of door flooding with respect to terrain, used to tell phone scanners where to scan. This morning it removed 92% of depth error from 11% of the street.
- A basin graph (ponds and spill heights) that agreed with the solver in 94 to 99% of cases and erred toward false alarms.
- Known weaknesses: the scan map shifted with LiDAR noise (41 to 62% agreement), single-patch barriers did nothing, drain inference failed, a cheap spill-point ranker was weak.

## 2. How I reasoned toward new ideas

I asked what flooding is underneath the solver, then looked for a field that already has good tools for that structure.

| First-principles observation | Field with matching tools | Idea |
|---|---|---|
| A pond's spill level is the lowest pass on any route out. That is a shortest-path problem with max in place of plus. | Tropical (min, max) algebra | 1 |
| Water volume is conserved, so some outcomes are impossible whatever the dynamics. | Formal verification, bound propagation | 2 |
| The scan map is a gradient, and gradients of noisy inputs are noisy. | Randomised smoothing in adversarial ML | 3 |
| A worst-case storm search needs a notion of "plausible storm". | Generative weather models as a prior | 4 |
| Ponds merging as rain rises looks like a connectivity transition. | Percolation in statistical physics | 5 |
| A single bump fails because water goes round it. A shape might not. | Topology optimisation in structural engineering | 6 |
| A puddle outline is a contour of the terrain, observed for free. | Seismic inversion, with vision models reading photos | 7 |
| A 1 m grid loses kerbs. Fluid dynamics handles lost scales with closure laws. | Turbulence closure, symbolic regression by LLM | 8 |
| The scan map is a function of terrain and imagery, so it can be learned. | Amortised inference, saliency models | 9 |
| The whole test loop is mechanical once kill lines are set. | AI maths playbook: propose, then verify | 10 |

Each idea got a kill line before any test ran.

## 3. What I tested and what happened

The earlier workspace was gone, so I rebuilt the solver and a street generator first.
Solver checks: water volume balances to 1 part in 100,000, and gradients match a finite-difference test to about 1%.

### Idea 2, certified dry: PASSED after one repair

Claim: a door stays dry if the storm's rain volume cannot fill the ground around it up to the threshold. No credit is taken for drains or outflow.

- First run, 20 streets, 320 door-and-storm cases: 2 violations. Both came from one door whose outside ground sat at or above its own threshold.
- Repair: refuse to certify a door like that.
- Validation with the repaired rule on 40 fresh streets: 0 violations in 640 cases.
- Coverage: 95% of dry cases certified.
- Tightness: the solver's flooding point was a median 1.21x the bound. 99% were within 2x.

A second certificate failed. "A still pond can never reach this door" was violated in 190 of 462 cases, because moving water rides above the still level. No violations occurred where the threshold cleared the still level by more than 12 cm in validation (0 of 86), and 1 of 62 in the first batch.

### Idea 1, min-max algebra: EXACT, speedup unproven

Claim: the fill level of every cell can be computed with (min, max) operations in parallel, matching the sequential method exactly.

- Seven terrains, from 12,288 to 1,048,576 cells. All three parallel forms matched sequential priority-flood exactly.
- Dense matrix squaring: 6 to 7 squarings for 280 to 739 basins. It is too heavy beyond a few thousand basins.
- Sparse basin-graph rounds: 239 rounds over 142,511 edges at 1 million cells. Naive grid sweeps needed 1,446.
- Sparse rounds grew with terrain size (29, 46, 95, 239), so the log(n) claim holds only for the dense form.
- CPU time at 1 million cells: 0.62 s for the graph route, 0.37 s for optimised sequential C. No speedup without a GPU.
- Physical check on six streets: the solver's settled water surface sat 6 to 12 mm above the computed fill level after 30 minutes, still draining.

Open part: this is full fill. Partial fill under a finite storm is untested.

### Idea 3, smoothed scan map: FAILED

Kill line: 80% agreement between scan maps from two LiDAR noise draws.

| Street | Agreement, single map | Agreement, smoothed | Error removed, single | Error removed, smoothed | Random scan |
|---|---|---|---|---|---|
| 1 | 41% | 58% | 37% | 77% | 12% |
| 2 | 52% | 59% | 30% | 18% | -1% |
| 3 | 38% | 35% | 95% | 93% | 3% |

Smoothing helped accuracy on one street, hurt on one, and was neutral on the third.

### Idea 6, optimised regrade: FAILED

Kill line: beat raising the door threshold per cubic metre of material.

| Street | No action | Threshold +10 cm (0.05 m3) | Regrade 0.05 m3 | Regrade 0.5 m3 | Regrade 4 m3 |
|---|---|---|---|---|---|
| 1 | 8.4 cm | 0 | 8.1 | 6.9 | 6.6 |
| 2 | 3.4 cm | 0 | 1.6 | 0.2 | 0 |

In the larger unseen storm the threshold raise still gave zero. The 4 m3 regrade left 10.2 and 18.3 cm.
One side effect: the 4 m3 regrade on street 1 cut flooding at other doors by 9 cm in total, which a threshold cannot do.
A third street did not finish.

### Not run

- Idea 5: skipped for time.
- Ideas 4, 7, 8, 9, 10: need radar data, photos, or model training I don't have here.

## 4. A warning for the headline claim

The plain gradient scan map removed 37%, 30% and 95% of depth error on my three rebuilt streets, averaged over two noise draws. This morning's figure was 92%.

- On street 1, one noise draw gave 86%, so the other was far worse. The map's value swings with the noise draw.
- My generator blurs door thresholds into the starting terrain. This morning's may not have, so the comparison isn't like for like.
- I tested whether forcing door blocks into the scan set fixes it. It helped on one street and hurt on another, so that explanation isn't supported.

Check the claim on the real Blackfriars tile with several noise draws before pitching "a tenth of the street".

## 5. Limits

- Streets are synthetic, from a generator I wrote today.
- Rain rates are very high effective rates standing in for run-on from a wider catchment.
- The solver is simplified, with simple gullies.
- No GPU timing exists for anything here.
- The certificate repair was chosen after seeing a failure. The 40-street validation is the fair test of it.
- I did not check any of the ten ideas against the literature for novelty.

## 6. What I would do next

1. Time idea 1 on the hack GPU. That gives the speedup number the judges ask for.
2. Build partial fill for idea 1, so it handles real storms.
3. Lead the pitch with idea 2: a flood model that ships with a guarantee, backed by 640 cases with no violation.
4. Re-test the scan map on real terrain before using the 92% figure.
5. Put the failures on one slide. These judges count informative negative results.

## 7. Files in this zip

- `floodlab.py`: street generator and differentiable solver.
- `sanity.py`: speed, mass balance and gradient checks.
- `test1_minmax.py`, `test2_cert.py`, `test3_smooth.py`, `test3b_doors.py`, `test6_regrade.py`: the tests.
- `res_*.json`, `*.log`: raw results.
- `README.md`: how to rerun each test.

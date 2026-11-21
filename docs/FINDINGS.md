# Findings so far (Saturday 18:52)

One page for anyone pulling the repository cold. Detail and timestamps are in `status/air.md` and `status/pro.md`. What to run next on the Pro is in `docs/PRO_PLAN.md`.

## What we are testing

Screening tools already say how much rain floods a point. We are testing whether we can show which few square metres of ground set that number for each building, how far away they are, and that a full 2D solver agrees when exactly those cells are changed and not otherwise. Around that sit three bets (`docs/BETS.md`) and an absorption extension (`docs/ABSORPTION.md`).

Site: 512 x 512 m at 1 m around Blackfriars Road and Southwark station. 207 receptors on building edges. Flooded means peak depth of 0.10 m at the receptor.

## Results, by status

### Holds

| Finding | Evidence |
|---|---|
| Which ground matters survives treating buildings as floodable footprints | Fill model: 28 of 29 buildings keep some of the same controlling ground, 1 keeps none (gate was 20%); 69% of active pairs stay active; critical rain falls a median 6 mm; building order kept (rank correlation 0.90) |
| **Every open square metre evaluated exactly** | 342,316 what-ifs in 603 s on 8 processes (14 ms per core under load); 5.2 days by rebuilding on one core. 2.7% of open ground (4,653 cells) moves any building; 78% of it is more than 5 m from the building it moves. Clean timing still to do |
| **Control experiment: ground the fill model dismisses does nothing in the solver** | 0 of 60 null patches and 0 of 30 random patches moved any receptor's peak by 1 cm, across three storms. As a screen over 120 patches: 22 flagged and active, 11 flagged and inactive, 0 missed, 87 correctly dismissed. Pass line was at most 10% |
| The solver is correct and reproducible | Matches the JAX reference to 0.002 mm; mass balance 1e-5; lake at rest exact; bit-identical across batch sizes |
| More rain never gives less peak water | 4 of 4 scaled-storm pairs at all 207 receptors; 10 of 10 envelope groups; no reversal in any depth sweep |
| The fill model gets settled water right | Against the solver's final depth: recall 85%, critical success index 83%; levels within 1.6 cm at the 90th percentile |
| Where both models give a building a critical rainfall, they agree | 30 buildings: fill minus solver median -0.3 mm, 24 of 30 within 5 mm |
| Changing the ground the fill model picks moves the water the predicted way | 21 of 21 remote patches (6 to 82 m from the building); rank correlation 0.91 between predicted and simulated change |
| Control is sparse in the fill model | 188 of 2,132 patch tests (9%) move any building's critical rainfall; one patch can move 29 of 32 at-risk buildings |
| Survey error moves critical rainfall, in the fill model | 5 cm error: median spread 5.9 to 6.7 mm with a fixed reference level. Error confined to ground more than 5 m from any receptor still gives 21% |
| Short-range error matters most; gentle tilts matter little | Threshold moving with the building's ground: 9.2 mm at 1 m, 9.7 at 3 m, 5.9 at 10 m, 3.1 at 30 m, 2.6 at 60 m. Threshold at a fixed level (overstates tilts): 4.3, 6.7, 6.1, 7.8, 11.5 |
| Knowing 1% of the ground cuts that spread, **in the solver too (pilot)** | 8 terrains, 22 receptors: spread 4.83 mm with nothing known, 3.33 mm with the chosen 1% known; ratio 0.69 against a line of 0.75. Bootstrap interval 0.46 to 1.01, and no random arm yet. Full run in progress |
| Knowing 1% of the ground cuts that spread; random ground does not (fill model) | Chosen from a 600-terrain ensemble: 40% cut on 100 unseen terrains (at the 40% line). Random 1%: 0%. 2% chosen: 51%. 5%: 59% |
| A harm-free set of small changes exists; the naive set harms neighbours. **Confirmed in the solver** | Five 5 cm patches (125 m2): all 5 predicted beneficiaries fall by 1 cm or more (up to 13.6 cm) and no receptor rises by 1 cm (largest 0.95 cm). The naive set chosen by benefit alone raises water by 1 cm or more at 7 receptors. One design; two of its patches are within 2 m of the receptor they help |
| An exact fast re-evaluation replaces a rebuild per patch (Bet 2) | `fill/sweep.py`: all 441,324 critical depths identical to brute force on the 2,132 patch tests; 6 ms per evaluation on one core once the machine was quieter (5,200 evaluations in 32 s), against 1.3 s by rebuilding: about 200x. Earlier, under heavy load: 20 to 31 ms |
| A plain derivative does not work here | Extrapolating the local slope to 5 cm recovers 65% of active patches with 29% false alarms; 114 of 175 active pairs respond in one direction only, and 1,300 of 2,132 patches create or remove a pit |
| The solver can model absorbing ground | `solver/flood_sink.py`: bit-identical with sinks off on a 128 x 128 crop; mass balance 1.6e-6 including absorbed water |

### Failed, and what replaced it

| What failed | Result | Consequence |
|---|---|---|
| **Control experiment: size and sign of the effect of flagged ground** | Sign right in 25 of 30 (line 26); rank correlation 0.51 (line 0.7); slope -0.12 (line 0.45 to 0.75) | The fill model is a screen for which ground can matter, not a predictor of how much. The failure is concentrated in the 15 mm storm; at 35 and 70 mm the rank correlation is 0.96 and 0.93 (seen after scoring) |
| Fill model as a screen to skip solver runs | Recall 66% against the solver's peak; almost no storm has all 207 receptors decided | Dropped. The fill model is used to find ground, not to replace the solver |
| Predicting the exact flip of a building, first test | 9 of 20 (line was 14) | Storms were placed with the fill model's critical depth, which is too high where water is in motion |
| Predicting the exact flip, retest on remote patches | 7 of 12 (line was 9) | Peak on unchanged ground predicted to 0.1 cm, but the fill model over-predicts the size of remote effects: slope 0.58 |
| A two-number physical correction for moving water | 6.6 cm error at the 90th percentile | Dropped |
| First way of choosing ground to measure (pass-cell patch tests) | 24% cut (line was 40%) | Replaced by the ensemble method above, tried after this failed; lines unchanged |

### Close

| Finding | Evidence | Caveat |
|---|---|---|
| Response curves have a simple three-number form (Bet 5) | 66% of 175 pairs fit within 0.5 mm at all 41 heights (pass 80%, kill 60%). 97 respond in one direction only; 98 have a dead band of 2 cm or more. Every active location moves some building with 5 cm or less; 38 with 1 cm | Some curves have more than one step. Fill model only |
| A learned correction for moving water | 48 unseen storms: recall 97%, critical success index 96%; 2.4 cm error at the 90th percentile (line was 2 cm) | One storm family only; tied to this terrain; not part of the headline |

### Running or waiting

| Experiment | Where | State |
|---|---|---|
| Absorption map from the fill model (E0) | Air CPU | Running |
| Friction, do-no-harm check, measure-where-it-matters pilot, absorption go/no-go | Pro GPU | See `docs/PRO_PLAN.md` |

## What the literature says we cannot claim

Full report: `reports/Flood absorption and terrain evidence.md`.

- **"Rain needed to flood a point" is prior art:** the Danish Blue Spot Model (2010), SCALGO Live's point query, and merge-tree flood queries by Rav, Lowe and Agarwal (2017). Speed is prior art too.
- **Not found, on a handful of searches each:** attributing a building's threshold to specific spill cells; choosing cells from the hierarchy and changing exactly those in a 2D solver; deciding where to re-survey; an exact sensitivity of fill-spill-merge.
- **Unread and most dangerous:** Lowe's 2021 Duke dissertation on uncertain terrains. The human is to check it.
- **Counter-evidence to address:** Abily et al. (2016) ranked terrain measurement error well below feature inclusion and resolution.

## Where our model departs from the Environment Agency's method

| Assumption | Ours | National method |
|---|---|---|
| Drainage loss | 12 mm/h from 100% of rain | 2013: 12 mm/h after cutting urban rain to 70%. 2025: 18 mm/h from 100% |
| Roof rain | Discarded | Falls on every cell |
| Buildings | Impassable walls | Footprints raised 0.3 m, floodable |
| Friction | 0.015 everywhere | About 0.02 tarmac, 0.03 grass (2013) |
| Flood threshold | 0.10 m | 0.15 m "in some areas", 0.30 m "likely"; floors about 0.20 m above ground |
| Terrain error | 5 cm, correlated over 3 m | 5 cm relative is supported; 3 m is not (one variogram gives 65 to 100 m) |
| Storm range | 10 to 120 mm in 15 to 60 min | UK record is 92 mm in an hour; 40 to 60 mm in an hour is rare but observed in London |

Decision (Mythos, `docs/mythos/6_decisions_after_research.md`): no baseline change tonight; disclose all of these; test buildings and friction as sensitivities. The claim is about which building floods first and which ground decides it, not absolute thresholds in mm.

## Absorption: what the sources support

- The ground at the site does not absorb in a short storm (London Clay under made ground and alluvium). Model every intervention as lined storage.
- Rain garden: 150 to 300 mm ponding, filter at 100 to 300 mm/h. Permeable paving: about 105 mm of storage in a 350 mm sub-base. Tree pit: about 3.9 m3 per tree at most. Canopy: 1 to 2 mm per storm.
- Do not claim that trees or grass reduce cloudburst flooding. The testable claim is about storage placed on flow paths.

## Wording rules

- Not "certified", "guaranteed" or "confirmed flips". Direction and rank were confirmed; flips were not.
- Not accuracy percentages that count dry cases. Use recall and critical success index.
- Not "LiDAR noise moves thresholds by tens of percent". Say unresolved kerb-and-threshold structure, and give mm of critical rain per cm of relative error.
- "We did not find", never "nobody has done".

# Findings so far (Saturday 16:50)

One page for anyone pulling the repository cold. Detail and timestamps are in `status/air.md` and `status/pro.md`. What to run next on the Pro is in `docs/PRO_PLAN.md`.

## What we are testing

Screening tools already say how much rain floods a point. We are testing whether we can show which few square metres of ground set that number for each building, how far away they are, and that a full 2D solver agrees when exactly those cells are changed and not otherwise. Around that sit three bets (`docs/BETS.md`) and an absorption extension (`docs/ABSORPTION.md`).

Site: 512 x 512 m at 1 m around Blackfriars Road and Southwark station. 207 receptors on building edges. Flooded means peak depth of 0.10 m at the receptor.

## Results, by status

### Holds

| Finding | Evidence |
|---|---|
| The solver is correct and reproducible | Matches the JAX reference to 0.002 mm; mass balance 1e-5; lake at rest exact; bit-identical across batch sizes |
| More rain never gives less peak water | 4 of 4 scaled-storm pairs at all 207 receptors; 10 of 10 envelope groups; no reversal in any depth sweep |
| The fill model gets settled water right | Against the solver's final depth: recall 85%, critical success index 83%; levels within 1.6 cm at the 90th percentile |
| Where both models give a building a critical rainfall, they agree | 30 buildings: fill minus solver median -0.3 mm, 24 of 30 within 5 mm |
| Changing the ground the fill model picks moves the water the predicted way | 21 of 21 remote patches (6 to 82 m from the building); rank correlation 0.91 between predicted and simulated change |
| Control is sparse in the fill model | 188 of 2,132 patch tests (9%) move any building's critical rainfall; one patch can move 29 of 32 at-risk buildings |
| Survey error moves critical rainfall, in the fill model | 5 cm error: median spread 5.9 to 6.7 mm with a fixed reference level. Error confined to ground more than 5 m from any receptor still gives 21% |
| It does not collapse at long correlation lengths, with a fixed reference | 4.3 mm at 1 m, 6.7 at 3 m, 6.1 at 10 m, 7.8 at 30 m, 11.5 at 60 m |
| Knowing 1% of the ground cuts that spread; random ground does not | Chosen from a 600-terrain ensemble: 40% cut on 100 unseen terrains (at the 40% line). Random 1%: 0%. 2% chosen: 51%. 5%: 59% |
| A harm-free set of small changes exists; the naive set harms neighbours | Fill model: five 5 cm patches lift 5 buildings and harm none; choosing by benefit alone harms 3 or 4 |
| The solver can model absorbing ground | `solver/flood_sink.py`: bit-identical with sinks off on a 128 x 128 crop; mass balance 1.6e-6 including absorbed water |

### Failed, and what replaced it

| What failed | Result | Consequence |
|---|---|---|
| Fill model as a screen to skip solver runs | Recall 66% against the solver's peak; almost no storm has all 207 receptors decided | Dropped. The fill model is used to find ground, not to replace the solver |
| Predicting the exact flip of a building, first test | 9 of 20 (line was 14) | Storms were placed with the fill model's critical depth, which is too high where water is in motion |
| Predicting the exact flip, retest on remote patches | 7 of 12 (line was 9) | Peak on unchanged ground predicted to 0.1 cm, but the fill model over-predicts the size of remote effects: slope 0.58 |
| A two-number physical correction for moving water | 6.6 cm error at the 90th percentile | Dropped |
| First way of choosing ground to measure (pass-cell patch tests) | 24% cut (line was 40%) | Replaced by the ensemble method above, tried after this failed; lines unchanged |

### Close

| Finding | Evidence | Caveat |
|---|---|---|
| A learned correction for moving water | 48 unseen storms: recall 97%, critical success index 96%; 2.4 cm error at the 90th percentile (line was 2 cm) | One storm family only; tied to this terrain; not part of the headline |

### Running or waiting

| Experiment | Where | State |
|---|---|---|
| Control experiment: 60 null, 30 random, 30 positive patches at 3 storms, pass lines committed first | Air GPU, Pro to take the far half | 15 of 46 chunk files at 16:45 |
| Exact one-sweep sensitivity of the depression tree (Bet 2) | Air, sub-agent | Being built |
| Absorption map from the fill model (E0) | Air CPU | Running |
| Correlation sweep with the threshold moving with the building's ground | Air CPU | Running |
| Buildings as 0.3 m floodable footprints, in the fill model | Air CPU | Queued; gate: more than 20% of buildings change controlling spill cell |
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

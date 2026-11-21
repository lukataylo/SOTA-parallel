# P1: the control experiment, with pass lines fixed before any run

Committed before the solver has run any of these cases. Cases and fill-model predictions are in `shared/p1_cases.npz`; built by `fill/p1_make.py` (random seed 777).

## Why

Every patch the solver has tested so far was one the fill model said would matter. So we do not know whether ground the fill model dismisses really does nothing, and the two earlier flip tests failed. This experiment asks one question: **is the fill model a valid screen for which ground matters?**

## Cases: 120 patches, each 5 x 5 m, raised or lowered 5 cm, at three storms

| Group | Count | How chosen |
|---|---|---|
| Null | 60 | Random from the 1,187 pass-cell patches that the fill model says change no receptor's depth by 1 mm in any of the three storms, at least 8 m from every receptor, not used before |
| Random | 30 | Random open-ground cells, random sign, no screening at all |
| Positive | 30 | Fill model predicts at least 1 cm of change at some receptor; at least 8 m from that receptor; not used before; spread evenly from the smallest to the largest predicted effect (1.0 to 32 cm) |

Storms: centred triangles, 40 minutes, net rain 15, 35 and 70 mm, plus 20 minutes after the rain. 363 solver runs.

## Pass lines

**Nulls.** At most 10% of the 60 null patches move any receptor's peak depth by 1 cm or more in any storm. (At most 6.)

**Positives.** For each positive patch, take the receptor and storm where the fill model predicts the largest change. Across the 30:
- the solver's change in peak depth has the predicted sign in at least 85% (at least 26 of 30);
- Spearman rank correlation between predicted and simulated change is at least 0.7;
- the slope of simulated on predicted change is between 0.45 and 0.75.

**Random patches** have no pass line. They are reported as they fall, split by what the fill model predicted for each.

## What will be reported regardless

Every case, including failures. Receptors inside or within 5 m of a patch are excluded from the null test, because moving the ground under a receptor changes its depth by definition.

## If it fails

The claim shrinks to: the fill model ranks leverage for buildings that flood by ponding, and sensitivity for buildings flooded by moving water needs the solver.
